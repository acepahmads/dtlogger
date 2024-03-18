import jwt
import json
import time
import logging
import requests
import channels.layers
import socket
import select
from os import environ as Env
from datetime import datetime
from django.db import models, connection
from django.apps import apps
from pymodbus.payload import BinaryPayloadDecoder, BinaryPayloadBuilder
from pymodbus.constants import Endian
from asgiref.sync import async_to_sync
from .enums import Statuses, Methods, Bytesizes, Parities, Stopbits, FunctionCodes, Outputs, DecodeOrders, DisplayTypes, IntegrationStatuses
from .helpers import AppHelper

logger = logging.getLogger("app")

class Config(models.Model):
  key = models.CharField(max_length=255, unique=True)
  name = models.CharField(max_length=255)
  value = models.TextField(blank=True, null=True)
  description = models.TextField(blank=True, null=True)
  status = models.CharField(max_length=5, choices=Statuses.choices, default=Statuses.ACTIVE)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  class Meta:
    db_table = "datalogger_configs"
  def __str__(self):
    return self.key
  @classmethod
  def value_by_key(self, key):
    try:
      config = self.objects.filter(key=key)
      return config.first().value if config.exists() else ""
    except:
      ""
  @classmethod
  def get_step(self):
    try:
      object_config = self.objects.filter(key="LAST_STEP")
      if object_config.exists():
        config = object_config.first()
        lifetime_last_step = Config.value_by_key("LIFETIME_LAST_STEP_IN_SECOND")
        if lifetime_last_step == "":
          lifetime_last_step = 30

        lifetime_duration = int(lifetime_last_step) - round((datetime.now() - config.updated_at).total_seconds())
        if lifetime_duration < 0:
          config.value = 0
          config.save()

      else:
        config = self.objects.create(key="LAST_STEP", name="LAST STEP", value=0, description="")

      return int(config.value)
    except:
      0
  @classmethod
  def update_step(self, step):
    try:
      object_config = self.objects.filter(key="LAST_STEP")
      if object_config.exists():
        config = object_config.first()
        config.value = step
        config.save()

      else:
        config = self.objects.create(key="LAST_STEP", name="LAST STEP", value=step, description="")

      return int(config.value)
    except:
      0

class Connection(models.Model):
  key = models.CharField(max_length=255, unique=True)
  name = models.CharField(max_length=255)
  method = models.CharField(max_length=5, choices=Methods.choices, default=Methods.RTU)
  port = models.CharField(max_length=255)
  baudrate = models.PositiveIntegerField(default=9600)
  bytesize = models.CharField(max_length=5, choices=Bytesizes.choices, default=Bytesizes.EIGHTBITS)
  parity = models.CharField(max_length=5, choices=Parities.choices, default=Parities.PARITY_NONE)
  stopbits = models.CharField(max_length=5, choices=Stopbits.choices, default=Stopbits.STOPBITS_ONE)
  timeout = models.DecimalField(default=0.1, max_digits=8, decimal_places=2)
  description = models.TextField(blank=True, null=True)
  status = models.CharField(max_length=5, choices=Statuses.choices, default=Statuses.ACTIVE)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  class Meta:
    db_table = "datalogger_connections"
  def __str__(self):
    return self.name
  def by_parameter_keys(keys):
    try:
      cursor = connection.cursor()
      cursor.execute('SELECT dc.id AS id, dc.method AS method, dc.port AS port, dc.baudrate AS baudrate, dc.bytesize AS bytesize, dc.parity AS parity, dc.stopbits AS stopbits, dc.timeout AS timeout FROM datalogger_connections dc, datalogger_sensors ds, datalogger_parameters dp WHERE dc.id = ds.connection_id AND ds.id = dp.sensor_id AND dc.status = 1 AND dp.key IN %(keys)s GROUP BY dc.id;', {'keys': tuple(keys)})
      result = AppHelper.fetchall(cursor)
      return result
    except:
      []
  def by_parameter_key(key):
    try:
      cursor = connection.cursor()
      cursor.execute('SELECT dc.id AS id, dc.method AS method, dc.port AS port, dc.baudrate AS baudrate, dc.bytesize AS bytesize, dc.parity AS parity, dc.stopbits AS stopbits, dc.timeout AS timeout FROM datalogger_connections dc, datalogger_sensors ds, datalogger_parameters dp WHERE dc.id = ds.connection_id AND ds.id = dp.sensor_id AND dc.status = 1 AND dp.key = %(key)s GROUP BY dc.id LIMIT 1;', {'key': key})
      result = AppHelper.fetchone(cursor)
      return result
    except:
      {}

class Sensor(models.Model):
  key = models.CharField(max_length=255, unique=True)
  name = models.CharField(max_length=255)
  connection = models.ForeignKey(Connection, on_delete=models.CASCADE, related_name="connection_id")
  uid = models.PositiveIntegerField(default=0)
  description = models.TextField(blank=True, null=True)
  status = models.CharField(max_length=5, choices=Statuses.choices, default=Statuses.ACTIVE)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  class Meta:
    db_table = "datalogger_sensors"
  def __str__(self):
    return f"{self.name} - UID {self.uid}"

class Parameter(models.Model):
  key = models.CharField(max_length=255, unique=True)
  name = models.CharField(max_length=255)
  sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name="sensor_id")
  function_code = models.CharField(max_length=5, choices=FunctionCodes.choices, default=FunctionCodes.READ_HOLDING_REGISTERS)
  output = models.CharField(max_length=5, choices=Outputs.choices, default=Outputs.READ_VALUE)
  decode_value = models.BooleanField(default=True, help_text="*Decode float 32bit<br/>Float AB CD (byteorder=Endian.Little, wordorder=Endian.Little)<br/>Float CD AB (byteorder=Endian.Little, wordorder=Endian.Big)<br/>Float BA DC (byteorder=Endian.Big, wordorder=Endian.Little)<br/>Float DC BA (byteorder=Endian.Big, wordorder=Endian.Big)<br/>Reference : https://stackoverflow.com/questions/30784965/pymodbus-read-write-floats-real")
  byteorder = models.CharField(max_length=5, choices=DecodeOrders.choices, default=DecodeOrders.ENDIAN_BIG)
  wordorder = models.CharField(max_length=5, choices=DecodeOrders.choices, default=DecodeOrders.ENDIAN_BIG)
  address = models.PositiveIntegerField(default=0)
  data_type = models.PositiveIntegerField(default=1)
  orchestrator_reduction = models.DecimalField(default=0, max_digits=50, decimal_places=25)
  orchestrator_factor = models.DecimalField(default=1, max_digits=10, decimal_places=5)
  factor = models.DecimalField(default=1, max_digits=10, decimal_places=5)
  formula = models.TextField(blank=True, null=True, help_text="*Formula akan dieksekusi sebagai code 'eval()', hasil eksekusi code akan diset pada variable 'value'")
  disabled_threshold = models.BooleanField(default=False)
  min_value = models.DecimalField(default=0.01, max_digits=10, decimal_places=5)
  max_value = models.DecimalField(default=99, max_digits=10, decimal_places=5)
  enable_orchestrator_calibration = models.BooleanField(default=True, help_text="*Untuk mengaktifkan fitur Calibration pada Instrument Orchestrator")
  enable_orchestrator_zeroing = models.BooleanField(default=False, help_text="*Untuk mengaktifkan fitur Zeroing pada Instrument Orchestrator")
  enable_ispu = models.BooleanField(default=False, help_text="*Hanya untuk Config 'MODULE_NAME' AQMS")
  description = models.TextField(blank=True, null=True)
  status = models.CharField(max_length=5, choices=Statuses.choices, default=Statuses.ACTIVE)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  class Meta:
    db_table = "datalogger_parameters"
  def __str__(self):
    return self.name

  def send_udp(message,parameter):
    try:
     UDP_IP = "127.0.0.1"
     UDP_PORT = 2024
     status = False
     #print("send message: %s" % message)
     #print("request")
     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
     message1=bytes(message,'ascii')
     sock.sendto(message1, (UDP_IP, UDP_PORT))
     sock.setblocking(0)
     ready = select.select([sock], [], [], 2)
     value="0"
     if ready[0]:
      value, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
      if parameter["output"] == "2":
       status = True
      #print("rcv data",data)
     sock.close()
    except socket.error:
     []
    return [value, status];
  def recv_udp():
    UDP_IP = "127.0.0.1"
    UDP_PORT = 2025
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.setblocking(0)
    ready = select.select([sock], [], [], 5)
    data=0
    print("ready to recv")
    if ready[0]:
     data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
     print("recv " % data)
    sock.close()
    return data

  def config_write(connection_id, key):
    try:
      cursor = connection.cursor()
      cursor.execute('SELECT dp.address as address, dp.data_type as data_type, ds.uid as uid, CONCAT("write", " ", ds.key, "#", dp.key) as keyid FROM datalogger_sensors ds, datalogger_parameters dp WHERE dp.sensor_id = ds.id AND ds.connection_id = %(connection_id)s AND dp.key = %(key)s LIMIT 1;', {"connection_id": connection_id, "key": key})
      result = AppHelper.fetchone(cursor)
      return result
    except:
      []
  def config_status(connection_id, key):
    try:
      cursor = connection.cursor()
      cursor.execute('SELECT CONCAT(dc.key, "-uid", ds.uid, "-address", dp.address, "-", "status", dc.id, ds.id, dp.id) as id, CONCAT("status", " ", ds.key, "#", dp.key) as keyid, dp.address as address, dp.decode_value as decode_value, dp.data_type as data_type, dp.byteorder as byteorder, dp.wordorder as wordorder, dp.min_value as min_value, dp.max_value as max_value, dp.factor as factor, dp.formula as formula, ds.uid as uid, dp.function_code as function_code, dp.output as output FROM datalogger_components dc, datalogger_items di, datalogger_sensors ds, datalogger_parameters dp WHERE dc.id = di.component_id AND di.parameter_id = dp.id AND dp.sensor_id = ds.id AND di.displayed = "2" AND ds.connection_id = %(connection_id)s AND dp.key = %(key)s LIMIT 1;', {"connection_id": connection_id, "key": key})
      result = AppHelper.fetchone(cursor)
      return result
    except:
      []
  def config_value(connection_id, key):
    try:
      cursor = connection.cursor()
      cursor.execute('SELECT CONCAT(dc.key, "-uid", ds.uid, "-address", dp.address, "-", "value", dc.id, ds.id, dp.id) as id, CONCAT("value", " ", ds.key, "#", dp.key) as keyid, dp.address as address, dp.decode_value as decode_value, dp.data_type as data_type, dp.byteorder as byteorder, dp.wordorder as wordorder, dp.min_value as min_value, dp.max_value as max_value, dp.disabled_threshold as disabled_threshold, dp.factor as factor, dp.formula as formula, dp.orchestrator_factor as orchestrator_factor, dp.orchestrator_reduction as orchestrator_reduction, ds.uid as uid, dp.function_code as function_code, dp.output as output FROM datalogger_components dc, datalogger_items di, datalogger_sensors ds, datalogger_parameters dp WHERE dc.id = di.component_id AND di.parameter_id = dp.id AND dp.sensor_id = ds.id AND di.displayed = "1" AND ds.connection_id = %(connection_id)s AND dp.key = %(key)s LIMIT 1;', {"connection_id": connection_id, "key": key})
      result = AppHelper.fetchone(cursor)
      return result
    except:
      []
  def get_active_sensors():
    try:
      cursor = connection.cursor()
      cursor.execute('SELECT dp.key, dp.name FROM datalogger_parameters dp WHERE dp.status = "1" AND dp.function_code in ("03", "04") AND dp.output = "1" AND dp.enable_orchestrator_calibration = TRUE')
      result = AppHelper.fetchall(cursor)
      return result
    except:
      []
  def get_active_sensor_by_key(key):
    try:
      cursor = connection.cursor()
      cursor.execute('SELECT dp.key, dp.name, dp.enable_orchestrator_zeroing, dp.orchestrator_factor FROM datalogger_parameters dp WHERE dp.status = "1" AND dp.function_code in ("03", "04") AND dp.output = "1" AND dp.enable_orchestrator_calibration = TRUE AND dp.key = %(key)s LIMIT 1;', {"key": key})
      result = AppHelper.fetchone(cursor)
      return result
    except:
      {}
  def writes(keys):
    results = []
    for connection in Connection.by_parameter_keys(keys):
      try:
        #client = AppHelper.modbus_connection(connection)
        #client.connect()
        for key in keys:
          results.append(Parameter.write(connection["id"], key))
        #client.close()
      except Exception as error:
        print("[ERROR] client write :", error)
    return results
  def write(connection_id, key):
    parameter = Parameter.config_write(connection_id, key)
    if parameter != {}:
      try:
        #client.write_register(parameter["address"], parameter["data_type"], unit = parameter["uid"])
        print("write",key)
        sQuery = "select * from datalogger_parameters where datalogger_parameters.key='"+key+"'"
        #print("sQuery:",sQuery)
        Parameter.send_udp(sQuery,parameter)
        time.sleep(0.1)
        write_status = True
      except Exception as error:
        print("[ERROR]", parameter["address"], error)
        write_status = False

      result = {
        "id": key,
        "write_status": write_status
      }

    else:
      result = {
        "id": key,
        "write_status": ""
      }

    return result

  def read_statuses(keys):
    results = []
    for connection in Connection.by_parameter_keys(keys):
      try:
        #client = AppHelper.modbus_connection(connection)
        #client.connect()
        for key in keys:
          results.append(Parameter.read_status(connection["id"], key))
        #client.close()
      except Exception as error:
        print("[ERROR] client read status :", error)
    return results
  def read_status(connection_id, key):
    parameter = Parameter.config_status(connection_id, key)
    result_status = "off"

    if parameter != {}:
      channel_layer = channels.layers.get_channel_layer()

      try:
        #read = Parameter.read_parameter(client, parameter)
        sQuery = "select * from datalogger_parameters where datalogger_parameters.key='"+key+"'"
        #print("sQuery:",sQuery)
        read=Parameter.send_udp(sQuery,parameter)
        value = read[0]
        status = read[1]

        if parameter["formula"] != "":
          check_result = eval(parameter["formula"])

        if check_result == True:
          result_status = "on"
        time.sleep(1)
      except Exception as error:
        print("[ERROR]", parameter["id"], error)

      result = {
        "id": parameter["id"],
        "status": result_status
      }
      async_to_sync(channel_layer.group_send)("socket-data" + Env.get("WS_CHANNEL_NAME", ""), {'type': 'send_data', 'data': {"items": [result]}})

    else:
      result = {
        "id": key,
        "status": result_status
      }

    return result
  def read_values(keys):
    results = []
    for connection in Connection.by_parameter_keys(keys):
      try:
        #client = AppHelper.modbus_connection(connection)
        #client.connect()
        for key in keys:
          print("read values", key)
          results.append(Parameter.read_value(connection["id"], key))
        #client.close()
      except Exception as error:
        print("[ERROR] client read values :", error)
    return results
  def read_value(connection_id, key):
    is_threshold_value = False
    parameter = Parameter.config_value(connection_id, key)
    #print("read value p")
    if parameter != {}:
      channel_layer = channels.layers.get_channel_layer()
      raw_value=0
      try:
        #print("parameter:",parameter)
        #read = Parameter.read_parameter(parameter)
        sQuery = "select * from datalogger_parameters where datalogger_parameters.key='"+key+"'"
        #print("sQuery:",sQuery)
        read=Parameter.send_udp(sQuery,parameter)
        #datar=Parameter.recv_udp()
        #print("data:",data)
        raw_value=float(read[0])
        value = raw_value
        value = value - float(parameter["orchestrator_reduction"])
        value = value * float(parameter["factor"])

        if parameter["formula"] != "":
          value = eval(parameter["formula"])

        value = value * float(parameter["orchestrator_factor"])
        #print("max", parameter["max_value"])
        if parameter["disabled_threshold"] == False and value > parameter["max_value"]:
          value = parameter["max_value"]
          is_threshold_value = True
        elif parameter["disabled_threshold"] == False and value < parameter["min_value"]:
          value = parameter["min_value"]
          is_threshold_value = True
        #print("write_bridge", parameter["max_value"])
        Parameter.write_bridge(connection_id, key, value)

        time.sleep(1)
      except Exception as error:
        print("[ERROR]", parameter["id"], error)
        value = parameter["min_value"]
        is_threshold_value = True
      print(key, "raw_value", raw_value, "value", value)
      result = {
        "id": parameter["id"],
        "raw_value": "{0:.3f}".format(raw_value),
        "value": "{0:.3f}".format(value),
        "is_threshold_value": is_threshold_value
      }
      #print("result:",result)
      async_to_sync(channel_layer.group_send)("socket-data" + Env.get("WS_CHANNEL_NAME", ""), {'type': 'send_data', 'data': {"items": [result]}})

    else:
      result = {
        "id": key,
        "value": "",
        "is_threshold_value": is_threshold_value
      }

    return result
  def read_original_value_by_keys(keys):
    results = []
    for connection in Connection.by_parameter_keys(keys):
      try:
        #client = AppHelper.modbus_connection(connection)
        #client.connect()
        for key in keys:
          results.append(Parameter.read_original_value(connection["id"], key))
        #client.close()
      except Exception as error:
        print("[ERROR] client read value :", error)
    return results
  def read_original_value_by_key(key):
    result = {}
    connection = Connection.by_parameter_key(key)
    try:
      #client = AppHelper.modbus_connection(connection)
      #client.connect()
      result = Parameter.read_original_value(connection["id"], key)
      #client.close()
    except Exception as error:
      print("[ERROR] client read value :", error)
    return result
  def read_original_value(client, connection_id, key):
    value = 0

    try:
      parameter = Parameter.config_value(connection_id, key)

      if parameter != {}:
        #read = Parameter.read_parameter(client, parameter)
        sQuery = "select * from datalogger_parameters where datalogger_parameters.key='"+key+"'"
        #print("sQuery:",sQuery)
        read=Parameter.send_udp(sQuery,parameter)
        value = read[0]

    except Exception as error:
      print("[ERROR]", key, error)

    return {
      "key": key,
      "value": "{0:.3f}".format(value)
    }

  def read_parameter(client, parameter):
    MAX_RETRY = 3
    actual_read_count = 0
    value = 0
    status = False
    keyid = ""

    while actual_read_count < MAX_RETRY:
      try:
        if parameter != {}:
          keyid = parameter["keyid"]
          parameter["byteorder_label"] = AppHelper.label(DecodeOrders, parameter["byteorder"])
          parameter["wordorder_label"] = AppHelper.label(DecodeOrders, parameter["wordorder"])

          if parameter["function_code"] == "03":
            registers_value = client.read_holding_registers(parameter["address"], parameter["data_type"], unit = parameter["uid"]).registers
          else:
            registers_value = client.read_input_registers(parameter["address"], parameter["data_type"], unit = parameter["uid"]).registers

          if parameter["decode_value"] == True:
            value = BinaryPayloadDecoder.fromRegisters(registers_value, byteorder = eval(str(parameter["byteorder_label"])), wordorder = eval(str(parameter["wordorder_label"]))).decode_32bit_float()
          else:
            value = registers_value[0]

          if parameter["output"] == "2":
            status = True

      except Exception as error:
        print("[ERROR]", keyid, error)

      if (parameter["output"] == "1" and value <= 0) or (parameter["output"] == "2" and status == False):
        actual_read_count += 1
        time.sleep(0.1)
      else:
        actual_read_count = MAX_RETRY

      return [value, status]
  def encode_value(connection_id, key, value):
    parameter = Parameter.config_value(connection_id, key)

    try:
      if parameter != {}:
        byteorder = AppHelper.label(DecodeOrders, parameter["byteorder"])
        wordorder = AppHelper.label(DecodeOrders, parameter["wordorder"])
        builder = BinaryPayloadBuilder(byteorder = eval(str(byteorder)), wordorder = eval(str(wordorder)))
        builder.add_32bit_float(value)
        payload = builder.to_registers()
        raw_values = [payload[i] for i in range (0, int(parameter["data_type"]))]
      else:
        raw_values = []
    except Exception as error:
      print("[ERROR]", key, error)

    return raw_values
  def write_bridge(connection_id, key, value):
    write_status = False
    key_bridge = key + "-bridge"
    connection = Connection.by_parameter_key(key_bridge)

    try:
      if connection != {}:
        parameter = Parameter.config_write(connection["id"], key_bridge)

        if parameter != {}:
          raw_values = Parameter.encode_value(connection_id, key, value)
          client = AppHelper.modbus_connection(connection)
          client.connect()
          client.write_registers(parameter["address"], raw_values, unit = parameter["uid"])
          client.close()
          write_status = True
    except Exception as error:
      print("[ERROR]", key_bridge, error)

    result = {
      "id": key,
      "write_status": write_status
    }

    return result

class Unit(models.Model):
  key = models.CharField(max_length=255, unique=True)
  label = models.CharField(max_length=255)
  description = models.TextField(blank=True, null=True)
  status = models.CharField(max_length=5, choices=Statuses.choices, default=Statuses.ACTIVE)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  class Meta:
    db_table = "datalogger_units"
  def __str__(self):
    return f"{self.key} - {self.label}"

class Component(models.Model):
  key = models.CharField(max_length=255, unique=True)
  name = models.CharField(max_length=255)
  description = models.TextField(blank=True, null=True)
  status = models.CharField(max_length=5, choices=Statuses.choices, default=Statuses.ACTIVE)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  class Meta:
    db_table = "datalogger_components"
    indexes = [
      models.Index(fields=["key", "status"], name="key_status_idx"),
      models.Index(fields=["name"], name="name_idx"),
    ]
  def __str__(self):
    return self.name
  def value_items(key):
    try:
      cursor = connection.cursor()
      cursor.execute('SELECT CONCAT(dc.key, "-uid", ds.uid, "-address", dp.address, "-", "value", dc.id, ds.id, dp.id) as id, di.label as label, FORMAT(dp.min_value, 3) as value, du.label as unit, dp.enable_ispu as enable_ispu FROM datalogger_components dc, datalogger_items di, datalogger_sensors ds, datalogger_parameters dp, datalogger_units du WHERE dc.id = di.component_id AND di.parameter_id = dp.id AND dp.sensor_id = ds.id AND di.unit_id = du.id AND dc.status = 1 AND di.status = 1 AND dc.key = %s;', [key])
      result = AppHelper.fetchall(cursor)
      return result
    except:
      []
  def status_items(key):
    try:
      cursor = connection.cursor()
      cursor.execute('SELECT CONCAT(dc.key, "-uid", ds.uid, "-address", dp.address, "-", "status", dc.id, ds.id, dp.id) as id, di.label as name, "off" as status FROM datalogger_components dc, datalogger_items di, datalogger_sensors ds, datalogger_parameters dp WHERE dc.id = di.component_id AND di.parameter_id = dp.id AND dp.sensor_id = ds.id AND dc.status = 1 AND di.status = 1 AND dc.key = %s;', [key])
      result = AppHelper.fetchall(cursor)
      return result
    except:
      []

class Item(models.Model):
  key = models.CharField(max_length=255, unique=True)
  label = models.CharField(max_length=255)
  component = models.ForeignKey(Component, on_delete=models.CASCADE, related_name="component_id")
  parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name="item_parameter_id")
  unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="unit_id")
  displayed = models.CharField(max_length=5, choices=DisplayTypes.choices, default=DisplayTypes.VALUE)
  description = models.TextField(blank=True, null=True)
  status = models.CharField(max_length=5, choices=Statuses.choices, default=Statuses.ACTIVE)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  class Meta:
    db_table = "datalogger_items"
  def __str__(self):
    return self.label

class Refrence(models.Model):
  identifier = models.CharField(max_length=255, unique=True)
  datetime = models.DateTimeField()
  uploaded_portal = models.CharField(max_length=5, choices=IntegrationStatuses.choices, default=IntegrationStatuses.WAITING)
  uploaded_klhk = models.CharField(max_length=5, choices=IntegrationStatuses.choices, default=IntegrationStatuses.WAITING)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  class Meta:
    db_table = "datalogger_refrences"
  def __str__(self):
    return self.identifier
  def last_refrence():
    try:
      cursor = connection.cursor()
      cursor.execute("SELECT dr.* FROM datalogger_refrences dr ORDER BY dr.datetime DESC LIMIT 1;")
      result = AppHelper.fetchone(cursor)
      return result
    except:
      {}
  def klhk_ready():
    try:
      cursor = connection.cursor()
      cursor.execute("SELECT dr.* FROM datalogger_refrences dr WHERE dr.uploaded_klhk IN ('1', '4') ORDER BY dr.datetime ASC LIMIT 1;")
      result = AppHelper.fetchone(cursor)
      return result
    except:
      {}
  def portal_ready():
    try:
      cursor = connection.cursor()
      cursor.execute("SELECT dr.* FROM datalogger_refrences dr WHERE dr.uploaded_portal IN ('1', '4') ORDER BY dr.datetime ASC LIMIT 1;")
      result = AppHelper.fetchone(cursor)
      return result
    except:
      {}
  def init_refrence():
    print("init_refrence C")
    #last_refrence = Refrence.last_refrence()
    #if last_refrence != {} and last_refrence["uploaded_portal"] == "1" and last_refrence["uploaded_klhk"] == "1" and Value.by_refrence(last_refrence["id"]) == []:
    #  refrence = Refrence.objects.get(id=last_refrence["id"])
    #  refrence.datetime = datetime.now()
    #  refrence.save()
    #  return refrence
    #else:
    #  date_time = datetime.now()
    #  refrence = Refrence.objects.create(identifier=date_time.strftime("%Y%m%d%H%M%S"), datetime=date_time)
    #  return refrence


class Value(models.Model):
  parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE, related_name="value_parameter_id")
  refrence = models.ForeignKey(Refrence, on_delete=models.CASCADE, related_name="refrence_id")
  raw_value = models.DecimalField(default=1, max_digits=8, decimal_places=2)
  value = models.DecimalField(default=1, max_digits=8, decimal_places=2)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  class Meta:
    db_table = "datalogger_values"
  def by_refrence(id):
    try:
      cursor = connection.cursor()
      cursor.execute("SELECT dv.* FROM datalogger_values dv WHERE dv.refrence_id = %s;", [id])
      result = AppHelper.fetchall(cursor)
      return result
    except:
      []
  def by_refrence_and_parameter(refrence, parameter):
    try:
      cursor = connection.cursor()
      cursor.execute("SELECT dv.* FROM datalogger_values dv, datalogger_refrences dr, datalogger_parameters dp WHERE dv.refrence_id = dr.id AND dr.identifier = %(refrence)s AND dp.id = dv.parameter_id AND dp.key = %(parameter)s ORDER BY dv.updated_at DESC, dv.value DESC LIMIT 1;", {"refrence": refrence, "parameter": parameter})
      result = AppHelper.fetchone(cursor)
      return result
    except:
      {}
  def save_values(keys):
    try:
      results = []
      refrence = Refrence.last_refrence()
      for key in keys:
        print("save values",[key])
        parameter_values = Parameter.read_values([key])
        parameter = Parameter.objects.get(key=key)
        parameter_value = float(parameter_values[0]["value"])
        value = Value.objects.create(refrence_id=refrence["id"], parameter_id=parameter.id, value=parameter_value, raw_value=parameter_value)
        results.append(value.id)
        print("[Save Value] Start", key)
        time.sleep(0.25)
    except:
      results = []

    return results

class Job(models.Model):
  key = models.CharField(max_length=255, unique=True)
  name = models.CharField(max_length=255)
  class_name = models.CharField(max_length=255)
  method_name = models.CharField(max_length=255)
  method_params = models.CharField(max_length=255, blank=True, null=True)
  sequence = models.PositiveIntegerField(default=1)
  description = models.TextField(blank=True, null=True)
  status = models.CharField(max_length=5, choices=Statuses.choices, default=Statuses.ACTIVE)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  class Meta:
    db_table = "datalogger_jobs"
  def __str__(self):
    return self.name
  def send_klhk():
    def value(parameter):
      try:
        object_value = Value.by_refrence_and_parameter(refrence.identifier, parameter)
        return float(object_value["value"])
      except:
        return 0.0

    try:
      counter=0
      refrence_klhk_ready = Refrence.klhk_ready()
      while refrence_klhk_ready != {}:
        refrence = Refrence.objects.get(identifier=refrence_klhk_ready["identifier"])
        refrence.uploaded_klhk = "2"
        refrence.save()
        print("[Send KLHK] Start", refrence.identifier)

        date = refrence.datetime
        url = Config.value_by_key("KLHK_URL")
        apikey = Config.value_by_key("KLHK_APIKEY")
        apisecret = Config.value_by_key("KLHK_APISECRET")
        station = Config.value_by_key("KLHK_STATION")
        params = eval(Config.value_by_key("KLHK_PARAMS"))

        request = requests.post(url, json = params)
        if request.status_code == 200:
          refrence.uploaded_klhk = "3"
          refrence.save()
          print("[Send KLHK] Finish", refrence.identifier, "successful with response", request.json())
        else:
          refrence.uploaded_klhk = "4"
          refrence.save()
          print("[Send KLHK] Finish", refrence.identifier, "failed with response", request.json())
        refrence_klhk_ready = Refrence.klhk_ready()
        time.sleep(0.2)
        counter+=1
        if (counter>100):
          break

      #else:
      #  print("[Send KLHK] data ready not found")

      time.sleep(2.5)
    except Exception as error:
      print(error)
  def send_portal():
    def value(parameter):
      try:
        object_value = Value.by_refrence_and_parameter(refrence.identifier, parameter)
        return float(object_value["value"])
      except:
        return 0.0

    try:
      counter=0
      refrence_portal_ready = Refrence.portal_ready()
      while refrence_portal_ready != {}:
        refrence = Refrence.objects.get(identifier=refrence_portal_ready["identifier"])
        #refrence.uploaded_portal = "2"
        #refrence.save()
        print("[Send Portal ] Start", refrence.identifier)

        date = refrence.datetime
        created_at = date.strftime("%Y-%m-%d %H:%M:%S +0700")
        updated_at = date.strftime("%Y-%m-%d %H:%M:%S +0700")
        url = Config.value_by_key("PORTAL_URL")
        token = Config.value_by_key("PORTAL_TOKEN")
        module_id = Config.value_by_key("PORTAL_MODULE_ID")
        station_id = Config.value_by_key("PORTAL_STATION_ID")
        headers = {
          "Authorization": f"Bearer {token}"
        }
        params = eval(Config.value_by_key("PORTAL_PARAMS"))

        request = requests.post(url, json = params, headers = headers)
        if request.status_code == 200:
          refrence.uploaded_portal = "3"
          refrence.save()
          print("[Send Portal] Finish", refrence.identifier, "successful with response", request.json())
        else:
          refrence.uploaded_portal = "4"
          refrence.save()
          print("[Send Portal] Finish", refrence.identifier, "failed with response", request.json())
      #else:
      #  print("[Send Portal] data ready not found")
        refrence_portal_ready = Refrence.portal_ready()
        time.sleep(0.2)
        counter+=1
        if (counter>1000):
           break


      time.sleep(2.5)
    except Exception as error:
      print(error)
  def send_klhk_2step():
    def value(parameter):
      try:
        object_value = Value.by_refrence_and_parameter(refrence.identifier, parameter)
        return float(object_value["value"])
      except:
        return 0.0

    try:
      refrence_klhk_ready = Refrence.klhk_ready()
      if refrence_klhk_ready != {}:
        refrence = Refrence.objects.get(identifier=refrence_klhk_ready["identifier"])
        refrence.uploaded_klhk = "2"
        refrence.save()
        print("[Send KLHK 2 STEP] Start", refrence.identifier)

        url_secret = Config.value_by_key("KLHK_SECRET_URL_2STEP")
        request_secret = requests.get(url_secret)
        response_secret = request_secret.text

        if request_secret.status_code == 200:
          print("[Send KLHK 2 STEP] Finish", refrence.identifier, "successful get secret with response", response_secret)

          int_datetime = int(refrence.datetime.strftime("%s"))
          url_klhk = Config.value_by_key("KLHK_URL_2STEP")
          payload = {"token": jwt.encode(eval(Config.value_by_key("KLHK_PARAMS_2STEP")), response_secret, algorithm="HS256")}

          request_klhk = requests.post(url_klhk, json = payload)
          response_klhk = request_klhk.text

          if request_klhk.status_code == 200:
            refrence.uploaded_klhk = "3"
            refrence.save()
            print("[Send KLHK 2 STEP] Finish", refrence.identifier, "successful with response", response_klhk)
          else:
            refrence.uploaded_klhk = "4"
            refrence.save()
            print("[Send KLHK 2 STEP] Finish", refrence.identifier, "failed with response", response_klhk)
        else:
          refrence.uploaded_klhk = "4"
          refrence.save()
          print("[Send KLHK 2 STEP] Finish", refrence.identifier, "failed get secret with response", response_secret)
      else:
        print("[Send KLHK 2 STEP] data ready not found")

      time.sleep(2.5)
    except Exception as error:
      print(error)
  def transform_data(params):
    try:
      source_param = params[0]
      target_param = params[1]
      print("[TRANSFORM DATA]", "parameter source", source_param, "and parameter target", target_param)
    except Exception as error:
      print(error)
  def send_klhk_aqms():
    def value(parameter):
      try:
        object_value = Value.by_refrence_and_parameter(refrence.identifier, parameter)
        return float(object_value["value"])
      except:
        return 0.0

    try:
      counter=0
      refrence_klhk_ready = Refrence.klhk_ready()
      while refrence_klhk_ready != {}:
        refrence = Refrence.objects.get(identifier=refrence_klhk_ready["identifier"])
        #refrence.uploaded_klhk = "2"
        #refrence.save()
        print("[Send KLHK AQMS]Start", refrence.identifier)

        klhk_config = eval(Config.value_by_key("KLHK_CONFIG"))
        request_token = requests.post(klhk_config['auth_url'], json = klhk_config['auth_body'])

        if request_token.status_code == 200:
          response_request_token = request_token.json()
          headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(response_request_token['token'])
          }
          send_data = requests.post(klhk_config['data_url'], json.dumps(klhk_config['data_body']), headers = headers)

          print("[Send KLHK AQMS]", refrence.identifier, "body", klhk_config['data_body'])
          print("[Send KLHK AQMS]", refrence.identifier, "headers", headers)

          if send_data.status_code == 200:
            response_send_data = send_data.json()
            if response_send_data['status'] == 1:
              refrence.uploaded_klhk = "3"
              refrence.save()
              print("[Send KLHK AQMS ] Finish", refrence.identifier, "successful with response", response_send_data)
              Job.send_udp_log("klhk#"+"identifier,"+refrence.identifier+"#status,success#message,"+str(klhk_config['data_body'])+"#")
            else:
              refrence.uploaded_klhk = "4"
              refrence.save()
              print("[Send KLHK AQMS] Finish", refrence.identifier, "failed with response", response_send_data)
              Job.send_udp_log("klhk#"+"identifier,"+refrence.identifier+"#status,failed "+response_send_data+"#message,"+str(klhk_config['data_body'])+"#")
          else:
            refrence.uploaded_klhk = "4"
            refrence.save()
            print("[Send KLHK AQMS] Finish", refrence.identifier, "failed with response", send_data)
            Job.send_udp_log("klhk#" + "identifier," + refrence.identifier + "#status,failed " + str(send_data) + "#message,"+
                         klhk_config['data_body'] + "#")
        else:
          refrence.uploaded_klhk = "4"
          refrence.save()
          print("[Send KLHK AQMS] Finish", refrence.identifier, "failed request token with response", request_token)
          Job.send_udp_log(
            "klhk#" + "identifier," + refrence.identifier + "#status,failed to request with token " + str(request_token) + "#message,"+
            klhk_config['data_body'] + "#")
        refrence_klhk_ready = Refrence.klhk_ready()
        time.sleep(0.2)
        counter += 1
        if (counter > 100):
          break
      #else:
      #  print("[Send KLHK AQMS] data ready not found")
      #  Job.send_udp_log("klhk#" + "identifier,null" + "#status,failed no data" + "#message,null#")

      time.sleep(2.5)
    except Exception as error:
      print(error)
  def send_udp_log(message):
    import socket
    UDP_IP = "127.0.0.1"
    UDP_PORT = 2040
    #print("UDP target IP: %s" % UDP_IP)
    #print("UDP target port: %s" % UDP_PORT)
    #print("message: %s" % message)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message1=bytes(message,'ascii')
    sock.sendto(message1, (UDP_IP, UDP_PORT))
    sock.close()

class Event(models.Model):
  key = models.CharField(max_length=255, unique=True)
  name = models.CharField(max_length=255)
  step = models.PositiveIntegerField()
  description = models.TextField(blank=True, null=True)
  status = models.CharField(max_length=5, choices=Statuses.choices, default=Statuses.ACTIVE)
  jobs = models.ManyToManyField(Job, db_table="datalogger_job_events")
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  class Meta:
    db_table = "datalogger_events"
  def __str__(self):
    return self.name
  def jobs_by_step(step):
    try:
      cursor = connection.cursor()
      cursor.execute('SELECT dj.class_name as "class", dj.method_name as "method", dj.method_params as "params" FROM datalogger_events de, datalogger_jobs dj, datalogger_job_events dje WHERE dj.id = dje.job_id AND de.id = dje.event_id AND dj.status = "1" AND de.status = "1" AND de.step = %s ORDER BY dj.sequence ASC', [step])
      result = AppHelper.fetchall(cursor)
      return result
    except:
      []

class Scheduler(models.Model):
  key = models.CharField(max_length=255, unique=True)
  name = models.CharField(max_length=255)
  class_name = models.CharField(max_length=255)
  method_name = models.CharField(max_length=255)
  method_params = models.CharField(max_length=255, blank=True, null=True)
  hour = models.CharField(max_length=5)
  minute = models.CharField(max_length=5)
  second = models.CharField(max_length=5)
  description = models.TextField(blank=True, null=True)
  status = models.CharField(max_length=5, choices=Statuses.choices, default=Statuses.ACTIVE)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)
  class Meta:
    db_table = "datalogger_schedulers"
  def __str__(self):
    return self.name
  @classmethod
  def active(self):
    return self.objects.filter(status="1")
  def exec(self):
    try:
      if AppHelper.is_present(self.method_params):
         getattr(apps.get_model(self.class_name), self.method_name)(self.method_params.split(","))
      else:
        getattr(apps.get_model(self.class_name), self.method_name)()

      logger.info("exec scheduler {} ...".format(self.key))
    except Exception as error:
      logger.error(error)
