from google.oauth2 import service_account
from googleapiclient.discovery import build
from delepwn.utils.output import print_color
from delepwn.utils.api import handle_api_ratelimit
import csv
import sys
import base64
import html
from io import StringIO
from datetime import datetime, timezone

class GmailManager:
    """Manage Gmail operations including listing and reading emails"""
    
    def __init__(self, service_account_file):
        """Initialize the Gmail Manager
        
        Args:
            service_account_file (str): Path to service account JSON key file
        """
        if not service_account_file:
            raise ValueError("Service account file path is required")
            
        self.SERVICE_ACCOUNT_FILE = service_account_file
        self.SCOPES = [
            'https://mail.google.com/',
        ]
        self.service = None
        self.current_user = None

    def initialize_service(self, impersonate_email):
        """Initialize the Gmail service with impersonation
        
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
        
        self.service = build('gmail', 'v1', credentials=credentials)
        self.current_user = impersonate_email

    def clean_text_for_csv(self, text):
        """Clean and format text for CSV output
        
        Args:
            text (str): Raw text to clean
            
        Returns:
            str: Cleaned and formatted text
        """
        if not text:
            return ''
            
        # Replace various newline formats
        text = text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
        
        # Replace multiple spaces with single space
        text = ' '.join(text.split())
        
        # Clean up common email formatting artifacts
        text = text.replace('[image:', '[').replace('⌐', '©')
        
        # Remove URLs
        text = text.replace('<https://', '<').replace('>', '')
        
        # Fix common encoding issues
        text = text.replace('«', "'").replace('Æ', "'")
        
        return text

    def get_message_body(self, msg):
        """Extract the message body from the email and clean it for CSV
        
        Args:
            msg (dict): The full message object from Gmail API
            
        Returns:
            str: The cleaned email body text
        """
        if 'payload' not in msg:
            return ''

        text = ''
        # Handle multipart messages
        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            # If no text/plain found, try the first part
            if not text and 'body' in msg['payload']['parts'][0]:
                if 'data' in msg['payload']['parts'][0]['body']:
                    text = base64.urlsafe_b64decode(msg['payload']['parts'][0]['body']['data']).decode('utf-8')
        # Handle single part messages
        elif 'body' in msg['payload']:
            if 'data' in msg['payload']['body']:
                text = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')
        
        if text:
            # Clean and format the text for CSV
            text = html.unescape(text)
            return self.clean_text_for_csv(text)
        
        return ''

    def check_keywords_in_message(self, msg, keyword):
        """Check if keyword appears exactly in any message field
        
        Args:
            msg (dict): Message object from Gmail API
            keyword (str): Exact phrase to search for
            
        Returns:
            bool: True if exact phrase is found in any field
        """
        # Get each field separately
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        to = next((h['value'] for h in headers if h['name'] == 'To'), '')
        body = self.get_message_body(msg)
        
        # Check each field individually for exact phrase (case insensitive)
        keyword = keyword.lower()
        return (
            keyword in subject.lower() or
            keyword in sender.lower() or
            keyword in to.lower() or
            keyword in body.lower()
        )

    @handle_api_ratelimit
    def list_messages(self, max_results=100, start_date=None, end_date=None, keyword=None):
        """List emails in the user's inbox in CSV format"""
        if not self.service:
            raise ValueError("Service not initialized")

        try:
            # Build query for date filtering
            query = []
            if start_date:
                try:
                    date = datetime.strptime(start_date, '%Y-%m-%d')
                    query.append(f'after:{date.strftime("%Y/%m/%d")}')
                except ValueError:
                    print_color("Invalid start date format. Use YYYY-MM-DD", color="red")
                    return

            if end_date:
                try:
                    date = datetime.strptime(end_date, '%Y-%m-%d')
                    query.append(f'before:{date.strftime("%Y/%m/%d")}')
                except ValueError:
                    print_color("Invalid end date format. Use YYYY-MM-DD", color="red")
                    return

            # Get messages
            results = self.service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=' '.join(query)
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print_color("No messages found.", color="yellow")
                return
            
            # Create a string buffer
            output = StringIO()
            writer = csv.writer(output, lineterminator='')
            
            # Write header
            writer.writerow(['From', 'Subject', 'Date', 'Message ID', 'Body'])
            print(output.getvalue(), end='\n')
            output.seek(0)
            output.truncate(0)
            
            for message in messages:
                # Get full message content
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                
                # Skip if keyword doesn't match
                if keyword and not self.check_keywords_in_message(msg, keyword):
                    continue

                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'No Date')
                body = self.get_message_body(msg)
                
                # Write message data
                writer.writerow([sender, subject, date, message['id'], body])
                print(output.getvalue(), end='\n')
                output.seek(0)
                output.truncate(0)

        except Exception as e:
            print_color(f"Error listing messages: {str(e)}", color="red")
            raise 