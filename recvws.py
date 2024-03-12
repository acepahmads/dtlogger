import asyncio
import websockets
import json
import mysql.connector
import numpy as np
import struct
import socket
import select

def send_udp(message):
    UDP_IP = "127.0.0.1"
    UDP_PORT = 2024
    status = False
    # print("send message: %s" % message)
    # print("request")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message1 = bytes(message, 'ascii')
    sock.sendto(message1, (UDP_IP, UDP_PORT))
    sock.close()

def getdata(key, value):
    try:
        print("getdata")
        connection = mysql.connector.connect(host='localhost',
                                             database='wqms_onlimo',
                                             user='cbi',
                                             password='cbipa55word')

        sql_select_Query = f"SELECT datalogger_parameters.key, sensor_id, address FROM datalogger_parameters where datalogger_parameters.key='{key}' order by datalogger_parameters.id asc"
        cursor = connection.cursor()
        cursor.execute(sql_select_Query)
        # get all records
        records = cursor.fetchall()
        print("Total number of rows in table: ", cursor.rowcount)

        print("\nPrinting each row")
        uid = ""
        uid1 = ""
        fco = "03"
        adr = ""
        val = float(value)
        #print("sval:", fval)
        #b = float.hex(fval)
        #print("b:", b)
        hval = hex(struct.unpack('<I', struct.pack('<f', val))[0])[2:]
        print("hval:", hval)

        for row in records:
            uid = hex(row[1])[2:]
            uid1 = f"0{uid}" if len(uid) == 1 else uid
            adr = hex(row[2])[2:]
            print("key = ", row[0])
            print("uid = ", row[1], uid1)
            print("adr = ", row[2], adr)
        dataudp = "calibration,"+uid1+fco+adr+hval
        print("dataudp:", dataudp)
        send_udp(dataudp)

    except mysql.connector.Error as e:
        print("Error reading data from MySQL table", e)
    finally:
        if connection.is_connected():
            connection.close()
            cursor.close()
            print("MySQL connection is closed")

async def handle_client_message(message, websocket):
    print("Received message from client1:", message)
    for key, value in message.items():
        print(key, ":", value)
        print("getdata")
        getdata(key, value)
    #adr = "ph"
    #val = "12.3"
    #getdata()
    # response = {"received_data": message}
    # await websocket.send(json.dumps(response))


async def send_and_receive_json(websocket):
    async for message in websocket:
        received_data = json.loads(message)
        await handle_client_message(received_data, websocket)

start_server = websockets.serve(send_and_receive_json, "localhost", 2050)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()

