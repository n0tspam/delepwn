import json
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Define the path to your service account key file
SERVICE_ACCOUNT_FILE = ''

# Define the scopes required
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Define the email you want to impersonate
IMPERSONATE_EMAIL = ''
# Load the service account key file
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Delegate authority to the impersonated user
credentials = credentials.with_subject(IMPERSONATE_EMAIL)

# Build the service object
service = build('calendar', 'v3', credentials=credentials)

# Define the calendar ID (usually the primary calendar of the impersonated email)
calendar_id = 'primary'
description = """


"""

# Define the meeting details
event = {}
}

# Insert the event into the calendar
event_result = service.events().insert(calendarId=calendar_id, body=event, sendUpdates='all').execute()

print(f"Event created: {event_result.get('id')}")