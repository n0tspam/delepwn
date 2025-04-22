import os
import yaml
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from delepwn.utils.output import print_color
from delepwn.utils.api import handle_api_ratelimit

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
        """Initialize the Calendar Query with impersonation"""
        if not impersonate_email:
            raise ValueError("Impersonation email is required")
            
        credentials = service_account.Credentials.from_service_account_file(
            self.SERVICE_ACCOUNT_FILE,
            scopes=self.SCOPES,
            subject=impersonate_email
        )
        
        self.service = build('calendar', 'v3', credentials=credentials)
        self.current_user = impersonate_email
        print_color(f"-> Querying Calendar for {impersonate_email}", color="cyan")

    @handle_api_ratelimit
    def list_events(self, start_date, end_date):
        """List events between specified dates"""
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
            print_color("-" * 50, color="blue")
            
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                timezone = event['start'].get('timeZone', '')
                creator = event['creator'].get('email', 'Unknown')
                attendees = event.get('attendees', [])
                total_attendees = len(attendees)
                summary = event.get('summary', 'No Title')

                print_color(f"Title: {summary}", color="white")
                print_color(f"Start: {start} {timezone}", color="white")
                print_color(f"ID: {event['id']}", color="white")
                print_color(f"Creator: {creator}", color="white")
                print_color(f"Attendees: {total_attendees}", color="white")
                print_color("-" * 50, color="blue")

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
        """Create a phishing calendar event from YAML configuration"""
        if not self.service:
            raise ValueError("Service not initialized")

        try:
            # Load and validate configuration
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)

            # Debug output for configuration
            print_color(f"\nLoaded configuration: {config_path}", color="cyan")

            event_config = config['event']
            send_notifications = event_config.get('send_notifications', True)
            
            # Build event object with required fields
            event = {
                'summary': event_config['summary'],
                'description': event_config['description']
            }
            
            # Add optional fields if present
            if 'start_time' in event_config:
                event['start'] = {
                    'dateTime': event_config['start_time'],
                    'timeZone': event_config.get('timezone', 'UTC')
                }
                
            if 'end_time' in event_config:
                event['end'] = {
                    'dateTime': event_config['end_time'],
                    'timeZone': event_config.get('timezone', 'UTC')
                }
                
            if 'location' in event_config:
                event['location'] = event_config['location']
                
            if 'attendees' in event_config:
                event['attendees'] = [{'email': email} for email in event_config['attendees']]
                print_color(f"\nConfigured attendees:", color="cyan")
                for attendee in event['attendees']:
                    print_color(f"  - {attendee['email']}", color="white")
                
            if 'reminder_minutes' in event_config or 'popup_minutes' in event_config:
                event['reminders'] = {
                    'useDefault': False,
                    'overrides': []
                }
                if 'reminder_minutes' in event_config:
                    event['reminders']['overrides'].append({
                        'method': 'email', 
                        'minutes': event_config['reminder_minutes']
                    })
                if 'popup_minutes' in event_config:
                    event['reminders']['overrides'].append({
                        'method': 'popup', 
                        'minutes': event_config['popup_minutes']
                    })

            # Add conference details if specified
            if 'conference_solution' in event_config:
                event['conferenceData'] = {
                    'createRequest': {
                        'requestId': f"meet-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                        'conferenceSolutionKey': {
                            'type': event_config['conference_solution']
                        }
                    }
                }

            print_color("\n-> Creating calendar event", color="cyan")
            print_color("Configuration:", color="blue")
            print_color(f"File: {config_path}", color="white")
            print_color(f"Notifications: {send_notifications}", color="white")

            # Create the event
            result = self.service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all' if send_notifications else 'none',
                conferenceDataVersion=1 if event_config.get('conference_solution') else 0
            ).execute()

            print_color("\nEvent created successfully", color="green")
            print_color("-" * 50, color="blue")
            print_color(f"ID: {result.get('id')}", color="white")
            if 'hangoutLink' in result:
                print_color(f"Meet Link: {result.get('hangoutLink')}", color="white")
            if 'attendees' in event:
                print_color(f"Added {len(event['attendees'])} attendee(s)", color="white")
                print_color("Attendees:", color="white")
                for attendee in event['attendees']:
                    print_color(f"-> {attendee['email']}", color="white")
            print_color(f"Email notifications: {'enabled' if send_notifications else 'disabled'}", color="white")
            print_color("-" * 50, color="blue")

            return result

        except Exception as e:
            print_color(f"Error creating event: {str(e)}", color="red")
            raise

        except FileNotFoundError:
            print_color(f"Configuration file not found: {config_path}", color="red")
            raise
        except yaml.YAMLError as e:
            print_color(f"Error parsing YAML configuration: {e}", color="red")
            raise
        except ValueError as e:
            print_color(f"Invalid configuration: {str(e)}", color="red")
            raise
        except Exception as e:
            print_color(f"Error creating event: {str(e)}", color="red")
            raise

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