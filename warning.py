import sys
import time
import requests
import datetime
import mysql.connector
import json

def send_telegram_message(url, chat_id, message):
    params = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.get(url, params=params)
    return response.json()

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
            print(json_data["url"], json_data["chat_id"])
            url = json_data["url"]
            chat_id = json_data["chat_id"]

        if ((url == "") or (chat_id == "")):
            print("please check telegram.txt config")
        else:
            response = send_telegram_message(url, chat_id, message)
            print(response)
    except FileNotFoundError:
        print("File 'telegram.txt' not found")

    except Exception as e:
        print("An error occurred:", e)

def getdata(fromd, to, value):
    try:
        print("getdata")
        connection = mysql.connector.connect(host='localhost',
                                             database='wqms_onlimo',
                                             user='cbi',
                                             password='cbipa55word')

        #data transmission completeness checking
        now = datetime.datetime.now()
        startday1 = fromd
        startday = datetime.datetime.strptime(startday1, "%Y-%m-%d %H:%M:%S")
        duration = now - startday
        times = int(duration.seconds / 3600) - 1
        if (times < 0):
            times = 0
        print("Data must be sent ", times, " times")
        sql_select_Query = (f"SELECT datalogger_refrences.identifier FROM datalogger_refrences where datalogger_refrences.created_at between '{fromd}' and '{to}' and uploaded_klhk = '3' order by datalogger_refrences.id desc")
        print(sql_select_Query)
        cursor = connection.cursor()
        cursor.execute(sql_select_Query)
        # get all records
        records = cursor.fetchall()
        rows = cursor.rowcount
        print("data transmission completeness checking : ", rows)
        if (rows < times):
            message = f"{value} [{to}] : Data sent = {rows}, it should be {times}"
            send_warning_tele(message)

        #message waiting checking
        sql_select_Query = (f"SELECT datalogger_refrences.identifier FROM datalogger_refrences where datalogger_refrences.created_at between '{fromd}' and '{to}' and uploaded_klhk != '3' order by datalogger_refrences.id desc")
        print(sql_select_Query)
        #cursor = connection.cursor()
        cursor.execute(sql_select_Query)
        # get all records
        records = cursor.fetchall()
        rows = cursor.rowcount
        print("message waiting checking : ", rows)
        if (rows > 0):
            message = f"{value} [{to}] : {rows} sending message(s) is 'waiting/failed' to KLHK"
            send_warning_tele(message)

        #generate refrence checking
        sql_select_Query = (f"SELECT datalogger_refrences.identifier FROM datalogger_refrences where datalogger_refrences.created_at between '{fromd}' and '{to}' order by datalogger_refrences.id desc")
        print(sql_select_Query)
        #cursor = connection.cursor()
        cursor.execute(sql_select_Query)
        # get all records
        records = cursor.fetchall()
        rows = cursor.rowcount
        print("generate refrence checking : ", rows)
        if (rows == 0):
            message = f"{value} [{to}] : Fatal error, the system did not generate reference today, please check Immediately"
            send_warning_tele(message)

        if connection.is_connected():
            connection.close()
            cursor.close()
            print("MySQL connection is closed")

    except mysql.connector.Error as e:
        print("Error reading data from MySQL table", e)


def main(value):
    """
    try:
        value1 = 36.1
        print("value : ", value1)
        formula = "((3.76215537+0.52968523*value)/(1+0.06531247*value-0.00021621*(value**2))*0.0042)*((64/24.4)*1000)*0.73"
        print("formula : ", formula)

        value = eval(formula)
        print("value : ", value1)
    except Exception as error:
        print("An error occurred:", error)

    print("test12")
    """
    now = datetime.datetime.now()
    message = f"{value} [{now}] : The system is started"
    send_warning_tele(message)

    while (True):
        now = datetime.datetime.now()
        print(now)
        if ((now.minute == 0) and (now.second == 0)):
            print("minute 0")
            two_hour = datetime.timedelta(hours=2)
            two_hour_ago = now - two_hour
            fromd1 = two_hour_ago.strftime("%Y-%m-%d")
            fromd = str(fromd1) + " 00:00:00"
            print("from", fromd)

            one_hour = datetime.timedelta(hours=1)
            one_hour_ago = now - one_hour
            to1 = one_hour_ago.strftime("%Y-%m-%d %H:%M")
            to = str(to1) + ":00"
            print("to", to)

            getdata(fromd, to, value)
        time.sleep(1)
if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("invalid argument")


