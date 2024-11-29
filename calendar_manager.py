import os
import yaml
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.text_color import print_color

class CalendarManager:
    """Manage Google Calendar operations including listing, updating, and creating events"""
    
    def __init__(self, service_account_file):
        """Initialize the Calendar Manager
        
        Args:
            service_account_file (str): Path to service account JSON key file
        """
        if not service_account_file:
            raise ValueError("Service account file path is required")
            
        self.SERVICE_ACCOUNT_FILE = service_account_file
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.service = None
        self.current_user = None

    def initialize_service(self, impersonate_email):
        """Initialize the Calendar service with impersonation
        
        Args:
            impersonate_email (str): Email of the user to impersonate
        """
        if not impersonate_email:
            raise ValueError("Impersonation email is required")
            
        credentials = service_account.Credentials.from_service_account_file(
            self.SERVICE_ACCOUNT_FILE,
            scopes=self.SCOPES,
            subject=impersonate_email
        )
        
        self.service = build('calendar', 'v3', credentials=credentials)
        self.current_user = impersonate_email
        print_color(f"✓ Initialized calendar service for {impersonate_email}", color="green")

    def list_events(self, start_date, end_date):
        """List events between specified dates
        
        Args:
            start_date (datetime): Start date for listing events
            end_date (datetime): End date for listing events
        """
        if not self.service:
            raise ValueError("Service not initialized")

        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])

            if not events:
                print_color("No events found.", color="yellow")
                return

            print_color("\nEvents:", color="cyan")
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                timezone = event['start'].get('timeZone', '')
                creator = event['creator'].get('email', 'Unknown')
                attendees = event.get('attendees', [])
                total_attendees = len(attendees)
                summary = event.get('summary', 'No Title')

                print_color(f"\nEvent: {summary}", color="white")
                print_color(f"Start: {start} {timezone}", color="white")
                print_color(f"Event ID: {event['id']}", color="white")
                print_color(f"Creator: {creator}", color="white")
                print_color(f"Total Attendees: {total_attendees}", color="white")
                print_color("-" * 40, color="blue")

        except HttpError as error:
            print_color(f"Error listing events: {error}", color="red")

    def get_event_details(self, event_id):
        """Get detailed information about a specific event
        
        Args:
            event_id (str): ID of the event to retrieve
        """
        if not self.service:
            raise ValueError("Service not initialized")

        try:
            event = self.service.events().get(
                calendarId='primary', 
                eventId=event_id
            ).execute()

            print_color("\nEvent Details:", color="cyan")
            print_color(f"Summary: {event.get('summary', 'No Title')}", color="white")
            print_color(f"Start: {event['start'].get('dateTime', event['start'].get('date'))}", color="white")
            print_color(f"End: {event['end'].get('dateTime', event['end'].get('date'))}", color="white")
            print_color(f"Location: {event.get('location', 'No location')}", color="white")
            print_color(f"Description: {event.get('description', 'No description')}", color="white")
            
            if 'attendees' in event:
                print_color("\nAttendees:", color="cyan")
                for attendee in event['attendees']:
                    response = attendee.get('responseStatus', 'No response')
                    email = attendee.get('email', 'No email')
                    print_color(f"- {email} (Response: {response})", color="white")

        except HttpError as error:
            print_color(f"Error getting event details: {error}", color="red")

    def create_phishing_event(self, config_path):
        """Create a calendar event based on YAML configuration
        
        Args:
            config_path (str): Path to YAML configuration file
        """
        if not self.service:
            raise ValueError("Service not initialized")

        try:
            # Load configuration
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)

            event = {
                'summary': config['event']['summary'],
                'location': config.get('event', {}).get('location', ''),
                'description': config['event']['description'],
                'start': {
                    'dateTime': config['event']['start_time'],
                    'timeZone': config.get('event', {}).get('timezone', 'UTC'),
                },
                'end': {
                    'dateTime': config['event']['end_time'],
                    'timeZone': config.get('event', {}).get('timezone', 'UTC'),
                },
                'attendees': [{'email': email} for email in config['event']['attendees']],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': config.get('event', {}).get('reminder_minutes', 60)},
                        {'method': 'popup', 'minutes': config.get('event', {}).get('popup_minutes', 30)}
                    ],
                }
            }

            # Add optional conference details if specified
            if config.get('event', {}).get('conference_solution'):
                event['conferenceData'] = {
                    'createRequest': {
                        'requestId': f"meet-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                        'conferenceSolutionKey': {
                            'type': config['event']['conference_solution']
                        }
                    }
                }

            event_result = self.service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all',
                conferenceDataVersion=1 if config.get('event', {}).get('conference_solution') else 0
            ).execute()

            print_color(f"\n✓ Event created successfully", color="green")
            print_color(f"Event ID: {event_result['id']}", color="white")
            if 'hangoutLink' in event_result:
                print_color(f"Meet Link: {event_result['hangoutLink']}", color="white")

        except FileNotFoundError:
            print_color(f"Configuration file not found: {config_path}", color="red")
        except yaml.YAMLError as e:
            print_color(f"Error parsing YAML configuration: {e}", color="red")
        except HttpError as error:
            print_color(f"Error creating event: {error}", color="red")

    def update_event(self, event_id, summary=None, description=None, location=None):
        """Update specific fields of an event
        
        Args:
            event_id (str): ID of the event to update
            summary (str, optional): New summary for the event
            description (str, optional): New description for the event
            location (str, optional): New location for the event
        """
        if not self.service:
            raise ValueError("Service not initialized")

        try:
            # Get the existing event
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()

            # Update specified fields
            if summary:
                event['summary'] = summary
            if description:
                event['description'] = description
            if location:
                event['location'] = location

            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='none'
            ).execute()

            print_color(f"\n✓ Event updated successfully", color="green")
            print_color(f"Event ID: {event_id}", color="white")

        except HttpError as error:
            print_color(f"Error updating event: {error}", color="red")

    def delete_event(self, event_id):
        """Delete a specific event
        
        Args:
            event_id (str): ID of the event to delete
        """
        if not self.service:
            raise ValueError("Service not initialized")

        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            print_color(f"\n✓ Event deleted successfully", color="green")
            print_color(f"Event ID: {event_id}", color="white")

        except HttpError as error:
            print_color(f"Error deleting event: {error}", color="red")