import sys
import time
import requests
import datetime
import mysql.connector
import socket
import json


def send_udp_log(message):
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


def save_value(data, sql):
    try:
        print("save value")
        mydb = mysql.connector.connect(host='localhost',
                                             database='aqms',
                                             user='cbi',
                                             password='cbipa55word')

        mycursor = mydb.cursor()

        # Execute the query for each data tuple
        mycursor.executemany(sql, data)

        # Commit the changes
        mydb.commit()

        # Print the number of inserted rows
        print(mycursor.rowcount, "record(s) inserted.")

        # Close the connection
        mydb.close()

        if mydb.is_connected():
            mydb.close()
            mycursor.close()
            print("MySQL connection is closed")

    except mysql.connector.Error as e:
        print("Error reading data from MySQL table", e)


def main():
    #insert into datalogger_values(raw_value, value, created_at, updated_at, parameter_id, refrence_id, processing_state, type)
    #values('216', '2.150287', '2024-03-19 09:02:24', '2024-03-19 09:02:24', 22, 1, '1', '1')
    #{"parameter_id": 1, "raw_value": 68, "disabled_threshold": 0, "orchestrator_reduction": 0.0000000000000000000000000,
    # "orchestrator_factor": 1.00000, "min_value": 0.00000, "max_value": 1000.00000,
    # "formula": "(0.00261299*value+0.59324885)*((64/24.4)*10)*0.25"}

    UDP_IP = "127.0.0.1"
    UDP_PORT = 2042
    sock = socket.socket(socket.AF_INET,  # Internet
    socket.SOCK_DGRAM)  # UDP
    sock.bind((UDP_IP, UDP_PORT))
    while True:
        try:
            data, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
            print(data)
            json_data = json.loads(data)
            print(json_data["parameter_id"], json_data["raw_value"], json_data["disabled_threshold"],
                  json_data["orchestrator_reduction"], json_data["orchestrator_factor"], json_data["min_value"], json_data["max_value"], json_data["formula"])

            raw_value = float(json_data["raw_value"])
            value = raw_value
            value = value - float(json_data["orchestrator_reduction"])
            value = value * float(json_data["factor"])

            if json_data["formula"] != "":
              value = eval(json_data["formula"])

            value = value * float(json_data["orchestrator_factor"])
            #print("max", parameter["max_value"])
            if json_data["disabled_threshold"] == False and value > json_data["max_value"]:
              value = json_data["max_value"]
            elif json_data["disabled_threshold"] == False and value < json_data["min_value"]:
              value = json_data["min_value"]
            print(value)

            now = datetime.datetime.now()
            data = [
                (raw_value, value, now, now, json_data["parameter_id"], "1", "1", "1")
            ]

            sql = "insert into datalogger_values(raw_value, value, created_at, updated_at, parameter_id, refrence_id, processing_state, type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            print(sql, data)
            save_value(data, sql)
        except Exception as error:
            print("[ERROR]", error)
            send_udp_log("inputmodbus#" + "E "+str(error))

if __name__ == "__main__":
    main()
    """
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("invalid argument")
    """

