from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from utils.text_color import print_color

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
        self.SCOPES = [
            'https://www.googleapis.com/auth/admin.directory.user',
            'https://www.googleapis.com/auth/admin.directory.user.security'
        ]
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

    def make_user_admin(self, target_email):
        """Elevate a user to super admin status
        
        Args:
            target_email (str): Email of the user to make admin
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First get the user to ensure they exist and get their ID
            try:
                user = self.service.users().get(userKey=target_email).execute()
            except HttpError as e:
                if e.resp.status == 404:
                    print_color(f"User {target_email} not found", color="red")
                    return False
                raise

            # Update user to make them a super admin
            user_update = {
                'isAdmin': True,
                'primaryEmail': target_email
            }

            result = self.service.users().update(
                userKey=target_email,
                body=user_update
            ).execute()

            if result.get('isAdmin'):
                print_color(f"✓ Successfully made {target_email} a super admin", color="green")
                return True
            else:
                print_color(f"× Failed to make {target_email} an admin", color="red")
                return False

        except HttpError as error:
            if error.resp.status == 403:
                print_color("× Permission denied. The service account may not have sufficient privileges.", color="red")
            else:
                print_color(f"× Error updating user: {error}", color="red")
            return False
        except Exception as e:
            print_color(f"× An unexpected error occurred: {str(e)}", color="red")
            return False