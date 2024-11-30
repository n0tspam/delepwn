from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.text_color import print_color
import random
import string

class AdminManager:
    """Manage Google Workspace Admin operations for elevating user privileges"""
    
    def __init__(self, service_account_file):
        """Initialize the Admin Manager
        
        Args:
            service_account_file (str): Path to service account JSON key file
        """
        if not service_account_file:
            raise ValueError("Service account file path is required")
            
        self.SERVICE_ACCOUNT_FILE = service_account_file
        self.SCOPES = ['https://www.googleapis.com/auth/admin.directory.user']
        self.service = None
        self.current_user = None

    def initialize_service(self, impersonate_email):
        """Initialize the Admin Directory service with impersonation
        
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
        
        self.service = build('admin', 'directory_v1', credentials=credentials)
        self.current_user = impersonate_email
        print_color(f"✓ Initialized admin service for {impersonate_email}", color="green")

    def create_admin_user(self, email):
        """Create a new admin user
        
        Args:
            email (str): Full email address for the new admin
            
        Returns:
            tuple: (bool, str) Success status and password if successful
        """
        try:
            # Generate random password
            password = ''.join(random.SystemRandom().choice(
                string.ascii_uppercase + string.digits) for _ in range(12))
            
            # Create user body
            body = {
                'primaryEmail': email,
                'name': {
                    'givenName': 'GSuite',
                    'familyName': 'API-Admin'
                },
                'password': password
            }

            # Create the user
            print_color(f"\nAttempting to create new user {email}...", color="cyan")
            self.service.users().insert(body=body).execute()
            print_color(f"✓ Created user with password: {password}", color="green")

            # Make user an admin using makeAdmin API call
            print_color("Attempting to elevate user to admin...", color="cyan")
            self.service.users().makeAdmin(
                userKey=email,
                body={'status': True}
            ).execute()
            print_color("✓ Successfully granted admin privileges", color="green")

            return True, password

        except HttpError as error:
            if error.resp.status == 403:
                print_color("× Permission denied. The service account may not have sufficient privileges.", color="red")
            else:
                print_color(f"× Error creating admin user: {error}", color="red")
            return False, None
        except Exception as e:
            print_color(f"× An unexpected error occurred: {str(e)}", color="red")
            return False, None

    def make_user_admin(self, target_email):
        """Elevate an existing user to admin status
        
        Args:
            target_email (str): Email of the user to make admin
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First validate the user exists
            try:
                self.service.users().get(userKey=target_email).execute()
            except HttpError as e:
                if e.resp.status == 404:
                    print_color(f"× User {target_email} not found", color="red")
                    return False
                raise

            # Make user an admin using makeAdmin API call
            print_color(f"\nAttempting to elevate {target_email} to admin...", color="cyan")
            self.service.users().makeAdmin(
                userKey=target_email,
                body={'status': True}
            ).execute()
            print_color(f"✓ Successfully granted admin privileges to {target_email}", color="green")
            return True

        except HttpError as error:
            if error.resp.status == 403:
                print_color("× Permission denied. The service account may not have sufficient privileges.", color="red")
            else:
                print_color(f"× Error updating user: {error}", color="red")
            return False
        except Exception as e:
            print_color(f"× An unexpected error occurred: {str(e)}", color="red")
            return False