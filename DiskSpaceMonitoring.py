import logging
import subprocess
import sys
import re
import os
import json
import requests

myhost = os.uname()[1]
WEBHOOK = "https://hooks.slack.com/services/XXXX/XXXX/wertyui"
CRITICAL_THRESHOLD = 90
WARNING_THRESHOLD = 80

def check_disk_usage():
        usage_output = subprocess.check_output('df -h', shell = True).decode('utf-8')
        #print (usage_output)
        usage_list = usage_output.split("\n")
        #print (usage_list)
        utilization_list = []
        for usage in usage_list:
                data_list = re.split('\s+',usage)
                #print data_list
                if len(data_list) == 6:
                        util_detail = {"FileSystem":None, "Size":None, "Used":None, "Avail":None, "Use%":None, "MountedOn":None, "Status":None}
                        util_detail['FileSystem'] = data_list[0]
                        util_detail['Size'] = data_list[1]
                        util_detail['Used'] = data_list[2]
                        util_detail['Avail'] = data_list[3]
                        util_detail['Use%'] = data_list[4]
                        util_detail['MountedOn'] = data_list[5]
                        if int(data_list[4].replace("%","")) > CRITICAL_THRESHOLD:
                                util_detail['Status'] = "Critical"
                        elif int(data_list[4].replace("%","")) > WARNING_THRESHOLD:
                                util_detail['Status'] = "Warning"
                        else:
                                util_detail['Status'] = "OK"
                        utilization_list.append(util_detail)
        return utilization_list

def create_payload(utilization_list):
        payload = []
        for util_detail in utilization_list:
                if util_detail['Status'] == "Critical" or util_detail['Status'] == "Warning":
                        payload.append(util_detail)
        return payload

def post_to_slack(payload, title):
        SERVER = " :server: " + myhost
        WARNING = " :caution-warning: "
        CRITICAL = " :alert3: "
        OK = " :ok: "

        slack_payload = SERVER + "\n"

        for item in payload:
                if item['Status'] == "Critical":
                        slack_payload = slack_payload + CRITICAL
                elif item['Status'] == "Warning":
                        slack_payload = slack_payload +  WARNING
                else:
                        slack_payload = slack_payload +  OK

                slack_payload = slack_payload + " Mounted On = " + item['MountedOn']  +" Usage = " +item['Use%'] + " Available = " + item['Avail'] + "\n"
        if payload:
                send_message(slack_payload, title)

def send_message(slack_payload, title):
        slack_data = {
                "username": "Autobots",
                "icon_emoji": ":autobots:",
                "attachments": [
                        {
                                "color": "#9733EE",
                                "fields": [
                                        {
                                                "title": title,
                                                "value": slack_payload,
                                                "short": "false",
                                        }
                                ]
                        }
                ]
        }
        byte_length = str(sys.getsizeof(slack_data))
        headers = {'Content-Type': "application/json", 'Content-Length': byte_length}
        response = requests.post(WEBHOOK, data=json.dumps(slack_data), headers=headers)
        if response.status_code != 200:
                raise Exception(response.status_code, response.text)

if __name__ == '__main__':
        if len(sys.argv) == 2:
                program, option = sys.argv
        else:
                option = "alert"
        utilization_list = check_disk_usage()
        payload = create_payload(utilization_list)
        if option == "REPORT":
                post_to_slack(utilization_list, "Disk Utilization Report :data-dictionary:")
        else:
                post_to_slack(payload, "Disk Utilization Alert :zap:")
