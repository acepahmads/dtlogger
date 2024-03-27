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
data_dict = {
    "cod": "",
    "bod": "",
    "toc": "",
    "tss": "",
    "turbidity": "",
    "ph": "",
    "amonia": "",
    "nitrat": "",
    "do": "",
    "salinity": "",
    "tds": "",
    "depth": "",
    "temperature": ""
}

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
        data_sent = int(duration.seconds / 3600) - int(h_hour)
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

def main():
    try:
        site = "CBI Instrumen"
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
            site = row
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
        print(now)
        if ((now.minute == 0) and (now.second == 0)):
        #if (now.second == 0):
            try:
                cod = 0.00
                bod = 0.00
                tss = 0.00
                flg = False
                conn = mysql.connector.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=database)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM datalogger_config_warning order by id asc")
                rows = cursor.fetchall()
                for row in rows:
                    now = datetime.datetime.now()
                    print("method:",row[1],"| expression:",row[3],"| h-hor:",row[2],"| key", row[4])
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
                                if (name == "cod"):
                                    cod = data_dict[f'{key}']
                                elif (name == "bod"):
                                    bod = data_dict[f'{key}']
                                elif (name == "tss"):
                                    tss = data_dict[f'{key}']
                if conn.is_connected():
                    cursor.close()
                    conn.close()
                if (flg == True):
                    names = data_dict.keys()
                    for row in rows:
                        for name in names:
                            if (name == row[4]):
                                print("cod", cod, "bod", bod, "tss", tss)
                                value = data_dict[f'{row[4]}']
                                if (value != ""):
                                    print("expression:", row[3], name, "value:", value)
                                    if (eval(row[3])):
                                        print(name,"Anomali")
                                    break
            except mysql.connector.Error as e:
                print("Error while connecting to MySQL", e)
            except Exception as e:
                print("An unexpected error occurred:", e)
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        time.sleep(1)
if __name__ == "__main__":

    main()


