from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import google.auth
import io
import csv

class DriveManager:
    """Class to manage Google Drive operations with domain-wide delegation"""
    
    def __init__(self, service_account_file):
        if not service_account_file:
            raise ValueError("Service account file path is required")
        self.SERVICE_ACCOUNT_FILE = service_account_file
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        self.service = None
        self.current_credentials = None
    
    def get_access_token(self, impersonate_email):
        """Create and return an access token for the impersonated user
        
        Args:
            impersonate_email: Email of the user to impersonate
            
        Returns:
            str: Access token
        """
        if not self.SERVICE_ACCOUNT_FILE:
            raise ValueError("Service account file path is not set")
            
        credentials = service_account.Credentials.from_service_account_file(
            self.SERVICE_ACCOUNT_FILE,
            scopes=self.SCOPES
        )
        
        if not impersonate_email:
            raise ValueError("Impersonation email is required")
            
        delegated_credentials = credentials.with_subject(impersonate_email)
        request = Request()
        delegated_credentials.refresh(request)
        return delegated_credentials.token

    def initialize_service(self, token):
        """Initialize the Drive service with the given token
        
        Args:
            token: Bearer token for authentication
        """
        if not token:
            raise ValueError("Token is required to initialize service")
            
        self.current_credentials = Credentials(token=token)
        self.service = build("drive", "v3", credentials=self.current_credentials)

    def download_file(self, file_id):
        """Download a file from Google Drive
        
        Args:
            file_id: ID of the file to download
            
        Returns:
            tuple: (file_name, file_content) or (None, None) if error occurs
        """
        if not self.service:
            raise ValueError("Service not initialized. Call initialize_service first.")
        
        if not file_id:
            raise ValueError("File ID is required")

        try:
            # Get file metadata
            file_metadata = self.service.files().get(
                fileId=file_id, 
                fields='name, mimeType'
            ).execute()
            
            print("Metadata: ", file_metadata)
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

                request = self.service.files().export_media(
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
                request = self.service.files().get_media(fileId=file_id)

            downloader = MediaIoBaseDownload(file, request)
            print("Downloader: ", downloader)
            
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
        """Return the file extension based on the mime type
        
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
        """Write file data to a CSV file
        
        Args:
            file_data: List of file data to write
            csv_filename: Name of the CSV file
        """
        if not csv_filename:
            raise ValueError("CSV filename is required")
            
        with open(csv_filename, mode='a', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(file_data)

    def list_files(self, output_file=None, folder_id=None):
        """List files in Google Drive
        
        Args:
            output_file: Optional file to write results to
            folder_id: Optional folder ID to list files from
            
        Returns:
            list: List of files if no output_file specified
        """
        if not self.service:
            raise ValueError("Service not initialized. Call initialize_service first.")

        try:
            all_files = []
            if folder_id:
                return self._list_files_in_folder(folder_id)

            page_token = None
            while True:
                response = self.service.files().list(
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
                        all_files.append({
                            'name': file_name,
                            'id': file_id,
                            'size': file_size,
                            'mime_type': mime_type,
                            'trashed': file_trashed
                        })
                        print(f"Name: {file_name}, ID: {file_id}, Size: {file_size}, "
                              f"Extension: {mime_type}, Trashed: {file_trashed}")

                page_token = response.get('nextPageToken')
                if not page_token:
                    break

            return all_files if not output_file else None

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
        except RefreshError:
            print("[*] Token refresh required")
            raise

    def _list_files_in_folder(self, folder_id):
        """List files in a specific folder
        
        Args:
            folder_id: ID of the folder
            
        Returns:
            list: List of files in the folder
        """
        if not folder_id:
            raise ValueError("Folder ID is required")
            
        query = f"'{folder_id}' in parents and trashed=false"
        try:
            results = self.service.files().list(
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
            print("[*] Token refresh required")
            raise