from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Path to the service account key file
SERVICE_ACCOUNT_FILE = ''

# Define the required scopes
SCOPES = ['https://www.googleapis.com/auth/drive']


# Your email address to share the files with
user_email = ''

# Function to set read permissions for a file or folder
def set_permissions(file_id, user_email, drive_service):
    try: 
        drive_service.permissions().create(
            fileId=file_id,
            body={'role': 'writer', 'type': 'user', 'emailAddress': user_email},
            sendNotificationEmail=False
        ).execute()
        print(f'Permission set for file/folder ID: {file_id}')
    except Exception as e:
        print(f'An error occurred: {e}')

# Function to recursively iterate through all files and folders
def iterate_and_set_permissions(folder_id, user_email, impersonated_email):
    # Create a credentials object from the service account file with domain-wide delegation
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES, subject=impersonated_email)

    drive_service = build('drive', 'v3', credentials=credentials)

    # List all files and folders in the current folder
    query = f"'{folder_id}' in parents"
    page_token = None

    while True:
        response = drive_service.files().list(q=query,
                                              spaces='drive',
                                              fields='nextPageToken, files(id, name, mimeType)',
                                              pageToken=page_token).execute()
        items = response.get('files', [])

        for item in items:
            # Set read permissions for each file and folder
            
        
            print("{} - {}".format(impersonated_email,item['name']))
            set_permissions(item['id'], user_email, drive_service)

            # If the item is a folder, recurse into the folder
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                iterate_and_set_permissions(item['id'], user_email, impersonated_email)

        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

# Root folder ID (use 'root' to refer to the root folder of the user's Drive)
root_folder_id = 'root'

# Email address of the user to whom you want to give read access

with open('', 'r') as file:
    email_addresses = file.read().splitlines()
    for impersonate_email in email_addresses:
        print("Starting with user: {}".format(impersonate_email))
        iterate_and_set_permissions(root_folder_id, user_email, impersonate_email)

print('Permissions set successfully for all items in the root folder.')