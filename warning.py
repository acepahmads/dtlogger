import sys
import time
import requests
import datetime
import mysql.connector

def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.get(url, params=params)
    return response.json()

def send_warning_tele(message):
    bot_token = "7013180303:AAEN1duZ6W4L__pBX6l32OnieQ-BZy6rSJ8"
    chat_id = "389139071"
    response = send_telegram_message(bot_token, chat_id, message)
    print(response)

def getdata(fromd, to, value):
    try:
        print("getdata")
        connection = mysql.connector.connect(host='localhost',
                                             database='wqms_onlimo',
                                             user='cbi',
                                             password='cbipa55word')

        #data transmission completeness checking
        now = datetime.datetime.now()
        startday = (str(now.date()) + " 00:00:00")
        startday = datetime.datetime.strptime(startday, "%Y-%m-%d %H:%M:%S")
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
            message = f"{value} [{now}] : incomplete send message(s) until now"
            send_warning_tele(message)

        #message waiting checking
        sql_select_Query = (f"SELECT datalogger_refrences.identifier FROM datalogger_refrences where datalogger_refrences.created_at between '{fromd}' and '{to}' and uploaded_klhk != '3' order by datalogger_refrences.id desc")
        print(sql_select_Query)
        cursor = connection.cursor()
        cursor.execute(sql_select_Query)
        # get all records
        records = cursor.fetchall()
        rows = cursor.rowcount
        print("message waiting checking : ", rows)
        if (rows > 0):
            message = f"{value} [{now}] : {records} message(s) waiting/failed to KLHK today"
            send_warning_tele(message)

        #generate refrence checking
        sql_select_Query = (f"SELECT datalogger_refrences.identifier FROM datalogger_refrences where datalogger_refrences.created_at between '{fromd}' and '{to}' order by datalogger_refrences.id desc")
        print(sql_select_Query)
        cursor = connection.cursor()
        cursor.execute(sql_select_Query)
        # get all records
        records = cursor.fetchall()
        rows = cursor.rowcount
        print("generate refrence checking : ", rows)
        if (rows == 0):
            message = f"{value} [{now}] : The system did not generate reference today"
            send_warning_tele(message)


    except mysql.connector.Error as e:
        print("Error reading data from MySQL table", e)
    finally:
        if connection.is_connected():
            connection.close()
            cursor.close()
            print("MySQL connection is closed")


def main(value):
    while (True):
        now = datetime.datetime.now()
        print(now)
        if (now.second == 0):
            print("minute 0")
            one_hour = datetime.timedelta(hours=1)
            one_hour_ago = now - one_hour
            formatted_time = one_hour_ago.strftime("%Y-%m-%d %H:%M")
            print("one hour ago", one_hour_ago)
            fromd = str(now.date()) + " 00:00:00"
            to = one_hour_ago
            getdata(fromd, to, value)
        time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Tidak ada argumen yang diberikan.")


