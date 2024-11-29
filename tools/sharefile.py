from google.oauth2 import service_account
from googleapiclient.discovery import build

# Path to the service account key file
SERVICE_ACCOUNT_FILE = ''
# The email of the user to impersonate
USER_EMAIL = ''
# Scopes required for the Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """Authenticate and create the Drive service with user impersonation."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
        subject=''
    )
    drive_service = build('drive', 'v3', credentials=credentials)
    return drive_service

def share_file_with_users(drive_service, file_id, email_list):
    """Share the file with a list of users."""
    for email in email_list:
        permissions = {
            'type': 'user',
            'role': 'writer',  # or 'reader', 'commenter'
            'emailAddress': email
        }
        try:
            response = drive_service.permissions().create(
                fileId=file_id,
                body=permissions,
                fields='id',
                sendNotificationEmail=False  # Disable email notifications
            ).execute()
            print(f'File shared with {email}, Permission ID: {response["id"]}')
        except Exception as e:
            print(f'An error occurred while sharing with {email}:', e)

def read_users_from_file(file_path):
    """Read user email addresses from a file."""
    with open(file_path, 'r') as file:
        email_list = file.read().splitlines()
    return email_list

def main():
    # File ID of the file you want to share
    file_id = ''
    # Path to the file containing the list of user email addresses
    users_file_path = ""
    
    drive_service = get_drive_service()
    email_list = read_users_from_file(users_file_path)
    share_file_with_users(drive_service, file_id, email_list)

if __name__ == '__main__':
    main()
