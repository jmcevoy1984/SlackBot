from slackclient import SlackClient
import datetime
import re
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_SCHEDULER_STARTED, EVENT_SCHEDULER_SHUTDOWN, EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import os
#import time
from flask import Flask


token = "your-token-here" # found at https://api.slack.com/web#authentication
sc = SlackClient(token) #Tokenizes the SlackClient for authentication.

bot_name = "Roster-Bot"
target_channel = '#general'
date_format = '{:[ %d-%m-%Y ]}'

roster_url = 'http://www.wonderfulwebsites.ie/roster/' #URL where the staff roster is displayed for the current day in HTML format.

#Get staff roster from indicated URL in HTML format.
def get_staff_roster():
    response = requests.get(roster_url)
    return response.content

#Strip HTML tags and format string accordingly using regex.
def get_formatted_roster():
    staff_members = {}
    re_pattern = '\[.+\]'
    response = requests.get(roster_url)
    found_result_list = re.findall(re_pattern, re.sub('In', '9am-6pm', str(get_staff_roster(), 'utf-8')))
    formatted_roster = re.sub('<\w+\/>', '#', found_result_list[0])
    formatted_roster = formatted_roster.split('#')
    for index, member in enumerate(formatted_roster):
        formatted_roster[index] = re.sub('\[|\]|\"', '', member).split(',')
        staff_members[formatted_roster[index][0]] = formatted_roster[index][1]
    return staff_members

def get_date_today_formatted():
    today = datetime.date.today()
    today_formatted = date_format.format(today)
    return today_formatted

def create_roster_attachment_data(staff_members):
    fields = []
    for name, shift in staff_members.items():
       field = {
       "title" : name,
       "value" : shift,
       "short" : "true"
       }
       fields.append(field)
    fields.append({"title" : ('-' * 70), "value" : ""}) #Footer made of dashes
    return fields

def get_usa_staff_count(staff_members):
    count = 0
    for shift in staff_members.values():
        if shift != "9am-6pm":
            count += 1
    return count

def generate_roster_footer(staff_members):
    total_staff_count = len(staff_members)
    us_staff_count = get_usa_staff_count(staff_members)
    footer_string = "Total Staff: "+str(total_staff_count)+"\nUS Shift Staff: "+str(us_staff_count)
    return footer_string

def date_and_time_now():
    now = datetime.datetime.now()
    time_format = '{:[%Y-%m-%d (%H:%M:%S)]: }'
    formatted_datetime = time_format.format(now)
    return formatted_datetime

#Defines the attachment as specced in the slack API to be sent along with the message to slack.
def create_attachment(data, footer):
    attachment = [
        {
            "title" : get_date_today_formatted() + '\n' + ('-' * 70), #Header with the formatted date followed by a line of dashes.
            "autor_name" : bot_name,
            "fields" : data,
            "color" : "good", #Preset value, green colour
            "footer" : footer,
            "fallback" : get_date_today_formatted()
        }
    ]
    return attachment

def is_slack_api_working():
    api_test_response = sc.api_call("api.test")
    if api_test_response['ok'] == True:
        print(date_and_time_now()+"Slack - API Test: OK.")
        return True
    else:
        print(date_and_time_now()+"Slack - API Test: Failed.")
        print("Error: "+api_test_response['error'])
        return False

def post_message(message_text, attachment, target_channel):
    if is_slack_api_working():
        api_call_response = sc.api_call(
            "chat.postMessage", channel=target_channel, text=message_text,
            username=bot_name, icon_emoji=':robot_face:', attachments=str(attachment).replace("'", '"')
        )
        if api_call_response['ok'] == True:
            print(date_and_time_now()+"Slack - Post Message To " + '"' + target_channel + '"' + ": OK.")
        else:
            print(date_and_time_now()+"Slack - Post Message To " + '"' + target_channel + '"' +": Failed.")
            print("Error: "+api_call_response['error'])

#Scheduler section: schedules the job that posts the message to the desired slack channel at the desired date/time.
def job_listener(event):
    if event.exception:
        print(date_and_time_now()+'Scheduler: Error - Job "'+event.job_id+'" sheduled to run at: '+event.scheduled_run_time+' crashed.')
        print(date_and_time_now()+'Traceback: '+event.traceback)
    else:
        print(date_and_time_now()+'Scheduler: Job "'+event.job_id+'" executed successfully.')

def scheduler_listener(event):
    if event.code == 1:
        print(date_and_time_now()+'Scheduler: Scheduler Started.')
    elif event.code == 2:
        print(date_and_time_now()+'Scheduler: Scheduler Shutdown.')


scheduler = BackgroundScheduler()
scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
scheduler.add_listener(scheduler_listener, EVENT_SCHEDULER_STARTED | EVENT_SCHEDULER_SHUTDOWN)
scheduler.add_job(post_message, 'cron',  day_of_week='mon-sat', hour=8, minute=59, end_date='2017-05-30', id='post_roster_to_'+target_channel, args=['*SUPPORT ROSTER*', create_attachment(create_roster_attachment_data(get_formatted_roster()), generate_roster_footer(get_formatted_roster())), target_channel])
scheduler.start()

app = Flask(__name__)
app.run()
'''print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

try:
    # This is here to simulate application activity (which keeps the main thread alive).
    while True:
        time.sleep(2)
except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
    scheduler.shutdown()'''


