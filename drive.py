import io
import csv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import google.auth

class DriveManager:
    """Class to manage Google Drive operations with impersonation capabilities"""
    
    def __init__(self, service_account_file=''):
        self.SERVICE_ACCOUNT_FILE = service_account_file
        self.SCOPES = ['https://www.googleapis.com/auth/drive']

    def get_access_token(self, impersonate):
        """Get access token for impersonation
        
        Args:
            impersonate: Email of the user to impersonate
        Returns:
            str: Access token
        """
        credentials = service_account.Credentials.from_service_account_file(
            self.SERVICE_ACCOUNT_FILE, 
            scopes=self.SCOPES
        )
        delegated_credentials = credentials.with_subject(impersonate)
        request = Request()
        delegated_credentials.refresh(request)
        return delegated_credentials.token

    def get_drive_service(self, token):
        """Create Google Drive service with credentials
        
        Args:
            token: Bearer token for authentication
        Returns:
            Resource: Google Drive service object
        """
        creds = Credentials(token=token)
        return build("drive", "v3", credentials=creds)

    def download_file(self, file_id, token):
        """Downloads a file from Google Drive
        
        Args:
            file_id: ID of the file to download
            token: Bearer token for authentication
        Returns:
            tuple: File name and content
        """
        service = self.get_drive_service(token)

        try:
            # Get file metadata
            file_metadata = service.files().get(
                fileId=file_id, 
                fields='name, mimeType'
            ).execute()
            
            print(f"Metadata: {file_metadata}")
            file_name = file_metadata.get('name')
            mime_type = file_metadata.get('mimeType')
            file = io.BytesIO()

            if mime_type.startswith('application/vnd.google-apps.'):
                # Handle Google Docs Editors files
                export_mime_type = {
                    'application/vnd.google-apps.document': 'application/pdf',
                    'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                }.get(mime_type, 'application/pdf')

                request = service.files().export_media(
                    fileId=file_id, 
                    mimeType=export_mime_type
                )
                
                file_extension = {
                    'application/pdf': '.pdf',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx'
                }.get(export_mime_type, '.pdf')
                
                file_name += file_extension
            else:
                # Handle binary files
                request = service.files().get_media(fileId=file_id)

            downloader = MediaIoBaseDownload(file, request)
            print(f"Downloader: {downloader}")
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}%.")

            if file.getvalue():
                with open(file_name, 'wb') as f:
                    f.write(file.getvalue())
                print(f'File downloaded as {file_name}')

            return file_name, file.getvalue()

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None, None

    def get_file_extension(self, mime_type):
        """Get file extension based on MIME type
        
        Args:
            mime_type: MIME type of the file
        Returns:
            str: File extension
        """
        mime_type_to_extension = {
            'application/vnd.google-apps.document': '.gdoc',
            'application/vnd.google-apps.spreadsheet': '.gsheet',
            'application/vnd.google-apps.presentation': '.gslides',
            'application/vnd.google-apps.drawing': '.gdraw',
        }
        return mime_type_to_extension.get(mime_type, '')

    def write_to_csv(self, file_data, csv_filename='files.csv'):
        """Write file data to CSV
        
        Args:
            file_data: Data to write
            csv_filename: Output CSV filename
        """
        with open(csv_filename, mode='a', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(file_data)

    def refresh_service(self, impersonate):
        """Refresh the Drive service with new token
        
        Args:
            impersonate: Email to impersonate
        Returns:
            Resource: Fresh Drive service
        """
        access_token = self.get_access_token(impersonate)
        creds = Credentials(token=access_token)
        try:
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"Exception occurred: {e}")
            return None

    def list_files_in_folder(self, service, folder_id):
        """List files in a specific folder
        
        Args:
            service: Drive service object
            folder_id: ID of the folder
        Returns:
            list: Files in the folder
        """
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
            return items
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
        except RefreshError:
            print("[*] Refreshing access token...")
            return []

    def list_files(self, bearer_token, output_file=None, folder_id=None):
        """List all files in Google Drive
        
        Args:
            bearer_token: Authentication token
            output_file: Optional CSV output file
            folder_id: Optional folder ID to list
        Returns:
            list: List of files
        """
        service = self.get_drive_service(bearer_token)
        all_files = []

        try:
            if folder_id:
                return self.list_files_in_folder(service, folder_id)

            page_token = None
            while True:
                response = service.files().list(
                    q="trashed=false",
                    spaces='drive',
                    fields='nextPageToken, files(id, name, size, mimeType)',
                    pageToken=page_token
                ).execute()

                files = response.get('files', [])
                for file in files:
                    file_name = file.get('name')
                    file_id = file.get('id')
                    file_size = file.get('size', 'N/A')
                    mime_type = file.get('mimeType')
                    file_extension = self.get_file_extension(mime_type)
                    file_trashed = file.get('trashed', False)

                    if output_file:
                        self.write_to_csv(
                            [file_name, file_id, file_size, file_trashed, mime_type], 
                            output_file
                        )
                    else:
                        print(f"Name: {file_name}, ID: {file_id}, Size: {file_size}, "
                              f"Extension: {mime_type}, Trashed: {file_trashed}")
                    all_files.append(file)

                page_token = response.get('nextPageToken')
                if not page_token:
                    break

            return all_files

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
        except RefreshError:
            print("[*] Refreshing access token...")
            service = self.refresh_service(service)
            return None