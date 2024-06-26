import sys
import argparse
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Path to the service account key file
SERVICE_ACCOUNT_FILE = ''

# Define the required scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

def list_events_for_date_range(service, user_email, start_date, end_date):
    """Lists the events on the user's calendar within the specified date range."""
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_date.isoformat() + 'Z',  # 'Z' indicates UTC time
        timeMax=end_date.isoformat() + 'Z',
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
        return

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        timezone = event['start'].get('timeZone', '')
        creator = event['creator'].get('email', 'Unknown')
        attendees = event.get('attendees', [])
        total_attendees = len(attendees)
        summary = event.get('summary', 'No Title')

        print(f"Event: {summary}")
        print(f"Start: {start} {timezone}")
        print(f"Event ID: {event['id']}")
        print(f"Creator: {creator}")
        print(f"Total Attendees: {total_attendees}")
        print('----------------------')
        print('')

def get_event_details(service, user_email, event_id):
    """Shows the details of a specific event."""
    try:
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        start = event['start'].get('dateTime', event['start'].get('date'))
        timezone = event['start'].get('timeZone', '')
        end = event['end'].get('dateTime', event['end'].get('date'))
        location = event.get('location', 'No location specified')
        description = event.get('description', 'No description')
        attendees = event.get('attendees', [])

        print(f"Event: {event['summary']}")
        print(f"Start: {start} {timezone}")
        print(f"End: {end}")
        print(f"Location: {location}")
        print(f"Description: {description}")
        print(f"Attendees:")
        for attendee in attendees:
            print(f"- {attendee['email']} (Response: {attendee.get('responseStatus', 'No response')})")
    except googleapiclient.errors.HttpError as error:
        print(f"An error occurred: {error}")

def update_event(service, user_email, event_id, new_summary=None, new_description=None, new_location=None):
    """Updates the specified fields of a specific event for the user."""
    conferenceDataVersionLocal = 0
    try:
        event = service.events().get(calendarId='primary', eventId=event_id).execute()

        # Update the specified fields
        if new_summary is not None:
            event['summary'] = new_summary
        if new_description is not None:
            event['description'] = new_description
        if new_location is not None:
            # Deletes the existing Conference link
            #print(event)
            if 'conferenceData' in event:
                del event['conferenceData']
                conferenceDataVersionLocal = 1
                print("Attempted to remove conference data. Only organizers can do this.")
            event['location'] = new_location

        updated_event = service.events().update(
            calendarId='primary',
            eventId=event_id,
            body=event,
            sendUpdates='none',  # No notifications
            conferenceDataVersion=conferenceDataVersionLocal
        ).execute()

        print(updated_event)
        print(f"Event updated for {user_email}.")
        if new_summary:
            print(f"New Summary: {new_summary}")
        if new_description:
            print(f"New Description: {new_description}")
        if new_location:
            print(f"New Location: {new_location}")
    except googleapiclient.errors.HttpError as error:
        print(f"An error occurred: {error}")

def delete_event(service, user_email, event_id):
    """Deletes a specific event for the user."""
    try:
        service.events().delete(calendarId='primary', eventId=event_id).execute()
        print(f"Event ID {event_id} deleted for {user_email}.")
    except googleapiclient.errors.HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Google Calendar API script')
    parser.add_argument('--start_date', type=str, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end_date', type=str, help='End date in YYYY-MM-DD format')
    parser.add_argument('--event_id', type=str, help='Event ID to get details for')
    parser.add_argument('--update_event_id', type=str, help='Event ID to update')
    parser.add_argument('--new_summary', type=str, help='New summary for the event')
    parser.add_argument('--new_description', type=str, help='New description for the event')
    parser.add_argument('--new_location', type=str, help='New location for the event')
    parser.add_argument('--delete', action='store_true', help='Delete the specified event')
    parser.add_argument('--user_email', type=str, required=True, help='Email of the user to impersonate')
    args = parser.parse_args()

    # Create a credentials object from the service account file with domain-wide delegation
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES, subject=args.user_email)

    # Build the Calendar API client
    service = build('calendar', 'v3', credentials=credentials)

    if args.event_id:
        # Show details of a specific event
        get_event_details(service, args.user_email, args.event_id)
    elif args.update_event_id:
        # Update the event for the specified fields
        update_event(service, args.user_email, args.update_event_id, args.new_summary, args.new_description, args.new_location)
    elif args.start_date and args.end_date:
        # Convert the input strings to datetime objects
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            print("Incorrect date format. Please use YYYY-MM-DD.")
            sys.exit(1)

        # List events for the specified date range for the impersonated user
        list_events_for_date_range(service, args.user_email, start_date, end_date)

    else:
        print("Usage: python your_script_name.py --start_date <start_date> --end_date <end_date> OR --event_id <event_id> OR --update_event_id <update_event_id> [--new_summary <new_summary>] [--new_description <new_description>] [--new_location <new_location>] OR --delete --update_event_id <update_event_id> --user_email <user_email>")
        sys.exit(1)
    if args.delete and args.update_event_id:
        # Delete the specified event
        delete_event(service, args.user_email, args.update_event_id)