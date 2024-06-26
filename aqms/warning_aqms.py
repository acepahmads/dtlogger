import sys
import time
import requests
import datetime
import mysql.connector
import json

host = 'localhost'
database = 'aqms'
user = 'cbi'
password = 'cbipa55word'
data_dict = {"test": ""}
data_dict1 = {"test1": ""}
def send_udp_log(message):
    try:
        import socket
        UDP_IP = "127.0.0.1"
        UDP_PORT = 2040
        # print("UDP target IP: %s" % UDP_IP)
        # print("UDP target port: %s" % UDP_PORT)
        # print("message: %s" % message)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        message1 = bytes(message, 'ascii')
        sock.sendto(message1, (UDP_IP, UDP_PORT))
        sock.close()
    except Exception as error:
      print("An error occurred:", error)

def send_telegram_message(url, chat_id, message):
    try:
        params = {
            "chat_id": chat_id,
            "text": message
        }
        response = requests.get(url, params=params)
        return response.json()
    except requests.RequestException as rerror:
        # Handle request exceptions
        print("An error occurred while sending the message:", rerror)
        send_udp_log("warning#" + "E send request telegram" + str(rerror))
        return None
    except Exception as error:
        # Handle other exceptions
        print("An unexpected error occurred:", error)
        send_udp_log("warning#" + "E send telegram" + str(error))
        return None

def send_warning_tele(message):
    try:
        url = ""
        chat_id = ""
        #{"url": "https://api.telegram.org/bot7013180303:AAEN1duZ6W4L__pBX6l32OnieQ-BZy6rSJ8/sendMessage",
        # "chat_id": "389139071"}
        with open('/home/cbi/dtlogger/config/telegram.txt', 'r') as file:
        #with open('telegram.txt', 'r') as file:
            # Read the entire contents of the file
            content = file.read()
            print(content)
            json_data = json.loads(content)
            print(message, json_data["url"], json_data["chat_id"])
            url = json_data["url"]
            chat_id = json_data["chat_id"]

        if ((url == "") or (chat_id == "")):
            print("please check telegram.txt config")
            send_udp_log("warning#" + "E please check telegram.txt config")
        else:
            response = send_telegram_message(url, chat_id, message)
            print(response)
    except FileNotFoundError:
        print("File 'telegram.txt' not found")
        send_udp_log("warning#" + "E File 'telegram.txt' not found")

    except Exception as error:
        print("An error occurred:", error)
        send_udp_log("warning#" + "E api telegram" + str(error))

def check_transmission(conn, site, sQuery, h_hour, msg, fromd, to):
    try:
        print(datetime.datetime.now())
        now = datetime.datetime.now()
        startday1 = fromd
        startday = datetime.datetime.strptime(startday1, "%Y-%m-%d %H:%M:%S")
        duration = now - startday
        data_sent = (int(duration.seconds / 3600) - int(h_hour)) * 2
        if (data_sent < 0):
            data_sent = 0
        print("Data must be sent", data_sent, "times")
        print(sQuery)
        cursor = conn.cursor()
        cursor.execute(sQuery)
        cursor.fetchall()
        count = cursor.rowcount
        print("data transmission completeness checking : ", count)
        if (count < data_sent):
            message = f"{site} [{to}] : " + eval(msg)
            send_warning_tele(message)
    except ValueError as ve:
        print("Value error occurred:", ve)
        send_udp_log("warning#" + "E Value" + str(ve))
    except Exception as e:
        print("An unexpected error occurred:", e)
        send_udp_log("warning#" + "E Value" + str(e))

def check_waiting(conn, site, sQuery, h_hour, msg, fromd, to):
    try:
        print(sQuery)
        cursor = conn.cursor()
        cursor.execute(sQuery)
        cursor.fetchall()
        rows = cursor.rowcount
        print("message waiting checking : ", rows)
        if (rows > 0):
            message = f"{site} [{to}] : " + eval(msg)
            send_warning_tele(message)
    except Exception as e:
        print("An unexpected error occurred:", e)
        send_udp_log("warning#" + "E check message waiting" + str(e))


def check_gen_refrence(conn, site, sQuery, h_hour, msg, fromd, to):
    try:
        print(sQuery)
        cursor = conn.cursor()
        cursor.execute(sQuery)
        cursor.fetchall()
        rows = cursor.rowcount
        print("generate refrence checking : ", rows)
        if (rows == 0):
            message = f"{site} [{to}] : " + eval(msg)
            send_warning_tele(message)
    except Exception as e:
        print("An unexpected error occurred:", e)
        send_udp_log("warning#" + "E check message waiting" + str(e))

def check_stuck(values, expression):
    last_value = values[0]
    count = 0
    ret = False
    for value in values:
        #print("value", value, "last_value", last_value)
        if value != last_value:
            count = 0
            last_value = value
        else:
            count += 1
        #print("counter", count)
        if (eval(expression)):
            ret = True
        else:
            ret = False
    return ret

def main(site):
    try:
        data_dict = {"test": ""}
        #site = "CBI Instrumen"
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM datalogger_configs where `key` = 'KLHK_STATION' LIMIT 1")
        rows = cursor.fetchone()
        for row in rows:
            print("config", row)
            #site = row

        cursor.execute("select `key` from datalogger_parameters where status='1' and function_code != '06' order by `key` asc")
        rows = cursor.fetchall()
        data_dict = {str(row[0]): "" for row in rows}
        print("dict", data_dict)
        if conn.is_connected():
            cursor.close()
            conn.close()

        now = datetime.datetime.now()
        message = f"{site} [{now}] : The system is started"
        send_warning_tele(message)
    except mysql.connector.Error as e:
        print("Error while connecting to MySQL", e)
        send_udp_log("warning#" + "E connecting to MySQL" + str(e))
    except Exception as e:
        print("An unexpected error occurred:", e)
        send_udp_log("warning#" + "E An unexpected error occurred" + str(e))

    while (True):
        now = datetime.datetime.now()
        #print(now)
        if ( ((now.hour == 0) or (now.hour == 12)) and (now.minute == 0) and (now.second == 0)):
        #if ((now.minute == 0) and (now.second == 0)):
        #if (now.second == 0):
            try:
                air_pressure = 0.00
                co = 0.00
                flow = 0.00
                hc = 0.00
                humidity = 0.00
                no2 = 0.00
                noise = 0.00
                o3 = 0.00
                pm10 = 0.00
                pm2_5 = 0.00
                rain_fall = 0.00
                so2 = 0.00
                solar_radiation = 0.00
                temperature = 0.00
                tvoc = 0.00
                w_speed = 0.00
                wind_angle = 0.00

                flg = False
                conn = mysql.connector.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=database)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM datalogger_config_warning order by id asc")
                rows = cursor.fetchall()
                message1 = ""
                for row in rows:
                    now = datetime.datetime.now()
                    print("\nmethod:", row[1], "| expression:", row[3], "| h-hor:", row[2], "| key", row[4], "| min_tolerance",
                          row[6], "| min_tolerance", row[7])
                    key = row[4]
                    expression = row[3]
                    hour1 = int(row[2])
                    hour2 = int(row[2])+1
                    hour3 = datetime.timedelta(hours=(hour2))
                    hour4 = now - hour3
                    fromd1 = hour4.strftime("%Y-%m-%d")
                    fromd = str(fromd1) + " 00:00:00"
                    print("from", fromd)

                    one_hour = datetime.timedelta(hours=(hour1))
                    one_hour_ago = now - one_hour
                    to1 = one_hour_ago.strftime("%Y-%m-%d %H:%M")
                    identifierfrom = one_hour_ago.strftime("%Y%m%d") + "000000"
                    identifiernow = one_hour_ago.strftime("%Y%m%d%H%M")+"00"
                    to = str(to1) + ":00"
                    print("to", to)
                    if ((row[1] == "send_klhk") or (row[1] == "send_portal")):
                        sQuery = f"SELECT datalogger_refrences.identifier FROM datalogger_refrences where datalogger_refrences.created_at between '{fromd}' and '{to}'"
                        if (expression!=""):
                            sQuery += f" and {expression}"
                        sQuery += " order by datalogger_refrences.id desc"
                        if ((row[4]) == "check_transmission"):
                            check_transmission(conn, site, sQuery, hour1, (row[5]), fromd, to)
                        elif ((row[4]) == "check_waiting"):
                            check_waiting(conn, site, sQuery, hour1, (row[5]), fromd, to)
                        elif ((row[4]) == "check_gen_refrence"):
                            check_gen_refrence(conn, site, sQuery, hour1, (row[5]), fromd, to)
                    elif (row[1] == "read_value"):
                        sQuery = ("select p.key, p.name, MAX(v.value) AS value from datalogger_values v "
                                  "inner join datalogger_refrences r on r.id = v.refrence_id "
                                  "inner join datalogger_parameters p on p.id = v.parameter_id "
                                  f"where r.identifier = '{identifiernow}' "
                                  #f"where r.identifier = '20240329130000' "
                                  f"and p.key = '{row[4]}' "
                                  "GROUP BY p.key, p.name order by p.name asc, left(r.identifier, 12) desc")
                        print(sQuery)
                        cursor.execute(sQuery)
                        rows1 = cursor.fetchall()
                        for row1 in rows1:
                            #print(row1[0], row1[2])
                            if row1[0] in data_dict:
                                data_dict[row1[0]] = row1[2]
                        names = data_dict.keys()
                        flg = True
                        #print("names in data_dict:", names)
                        #print("dt",data_dict[f'{key}'], key)
                        for name in names:
                            #print("name", name)
                            if (name == key):
                                print(name, data_dict[f'{key}'])
                                if (name == "air_pressure"):
                                    air_pressure = data_dict[f'{key}']
                                elif (name == "co"):
                                    co = data_dict[f'{key}']
                                elif (name == "flow"):
                                    flow = data_dict[f'{key}']
                                elif (name == "hc"):
                                    hc = data_dict[f'{key}']
                                elif (name == "humidity"):
                                    humidity = data_dict[f'{key}']
                                elif (name == "no2"):
                                    no2 = data_dict[f'{key}']
                                elif (name == "noise"):
                                    noise = data_dict[f'{key}']
                                elif (name == "o3"):
                                    o3 = data_dict[f'{key}']
                                elif (name == "pm10"):
                                    pm10 = data_dict[f'{key}']
                                elif (name == "pm2.5"):
                                    pm2_5 = data_dict[f'{key}']
                                elif (name == "rain_fall"):
                                    rain_fall = data_dict[f'{key}']
                                elif (name == "so2"):
                                    so2 = data_dict[f'{key}']
                                elif (name == "solar_radiation"):
                                    solar_radiation = data_dict[f'{key}']
                                elif (name == "temperature"):
                                    temperature = data_dict[f'{key}']
                                elif (name == "tvoc"):
                                    tvoc = data_dict[f'{key}']
                                elif (name == "w_speed"):
                                    w_speed = data_dict[f'{key}']
                                elif (name == "wind_angle"):
                                    wind_angle = data_dict[f'{key}']
                    elif (row[1] == "stuck_value"):
                        sQuery = ("select left(r.identifier, 12), p.name, count(v.value) as 'byk_data', "
                                  "ROUND(avg(v.value),4) as 'ratarata' from datalogger_values v "
                                  "inner join datalogger_refrences r on r.id = v.refrence_id "
                                  "inner join datalogger_parameters p on p.id = v.parameter_id "
                                  f"where r.identifier BETWEEN '{identifierfrom}' AND  '{identifiernow}' "
                                  f"and p.key = '{row[4]}' "
                                  "group by left(r.identifier, 12), p.name "
                                  "order by p.name asc, left(r.identifier, 12) desc")
                        print(sQuery)
                        cursor.execute(sQuery)
                        rows2 = cursor.fetchall()
                        valuestuck = []
                        for row2 in rows2:
                            valuestuck.append(row2[3])
                        print(valuestuck)
                        if (valuestuck != []):
                            if (check_stuck(valuestuck, row[3])):
                                print(row[4], "stuck")
                                message1 += "\n"
                                message1 += "[" + row[4] + " " + row[3] + "\n"
                                message1 += row[5] + "]"
                        else:
                            message1 += "\n"
                            message1 += "[" + row[4] + " no value" + "]"
                if conn.is_connected():
                    cursor.close()
                    conn.close()
                if (flg == True):
                    names = data_dict.keys()
                    for row in rows:
                        if (row[1] == "read_value"):
                            for name in names:
                                if (name == row[4]):
                                    value = data_dict[f'{row[4]}']
                                    print("\nchecking", name, value)
                                    print("expression:", row[3], name, "value:", value, "min", row[6], "max", row[7])
                                    expression = row[3]
                                    if (value != ""):
                                        min = 0
                                        max = 0
                                        if ((row[6] != "") and (row[6]) != None):
                                            min1 = eval(row[6])
                                            min = eval(min1)
                                        elif ((row[7] != "") and (row[7]) != None):
                                            max1 = eval(row[7])
                                            max = eval(max1)
                                        print("min", min, "max", max)
                                        lastvalue = value
                                        if (min > 0):
                                            value = float(value) + min
                                            print("value + min_tolerance", value, eval(row[3]))
                                            if (eval(str(eval(row[3])))):
                                                print(name, "Anomali")
                                                message1 += "\n"
                                                expression = eval(expression)
                                                print("expression", expression)
                                                message1 += "[" + name + " " + str(lastvalue) + " " + row[3] + ")\n"
                                                message1 += eval(row[5]) + "]"
                                        elif (max > 0):
                                            value = float(value) - max
                                            print("value - max_tolerance", max, eval(row[3]))
                                            if (eval(str(eval(row[3])))):
                                                print(name, "Anomali")
                                                message1 += "\n"
                                                expression = eval(expression)
                                                print("expression", expression)
                                                message1 += "[" + name + " " + str(lastvalue) + " " + row[3] + ")\n"
                                                message1 += eval(row[5]) + "]"
                                        else:
                                            if (eval(str(eval(row[3])))):
                                                print(name, "Anomali")
                                                message1 += "\n"
                                                expression = eval(expression)
                                                print("expression", expression)
                                                message1 += "[" + name + " " + str(lastvalue) + " " + row[3] + ")\n"
                                                message1 += eval(row[5]) + "]"
                                    else:
                                        if (message1 != ""):
                                            message1 += "\n"
                                        message1 += name + " no value"
                                    break
                if (message1 != ""):
                    message = f"{site} [{now}] : " + message1
                    print(message)
                    send_warning_tele(message)



            except mysql.connector.Error as e:
                print("Error while connecting to MySQL", e)
                send_udp_log("warning#" + "E Error while connecting to MySQL" + str(e))
            except Exception as e:
                print("An unexpected error occurred:", e)
                send_udp_log("warning#" + "E An unexpected error occurred:" + str(e))
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        time.sleep(1)
if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("invalid argument")

