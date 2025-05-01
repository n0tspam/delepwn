from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from delepwn.utils.output import print_color
import google.auth
import io
import csv
import os

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
                fields='name, mimeType, size'
            ).execute()
            
            print_color(f"\nDownloading file: {file_metadata.get('name')}", color="cyan")
            file_name = file_metadata.get('name')
            mime_type = file_metadata.get('mimeType')
            file_size = file_metadata.get('size', 'unknown')
            
            print_color(f"File type: {mime_type}", color="cyan")
            print_color(f"File size: {file_size} bytes", color="cyan")
            
            file = io.BytesIO()

            if mime_type.startswith('application/vnd.google-apps.'):
                # Handle Google Docs Editors files
                export_mime_type = {
                    'application/vnd.google-apps.document': 'application/pdf',
                    'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    'application/vnd.google-apps.drawing': 'application/pdf',
                    'application/vnd.google-apps.script': 'application/json',
                    'application/vnd.google-apps.form': 'application/pdf',
                    'application/vnd.google-apps.site': 'text/plain',
                }.get(mime_type)
                
                if not export_mime_type:
                    print_color(f"Warning: Unsupported Google Workspace file type: {mime_type}", color="yellow")
                    return None, None

                request = self.service.files().export_media(
                    fileId=file_id, 
                    mimeType=export_mime_type
                )
                
                file_extension = {
                    'application/pdf': '.pdf',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
                    'application/json': '.json',
                    'text/plain': '.txt'
                }.get(export_mime_type, '.pdf')
                
                if not file_name.endswith(file_extension):
                    file_name += file_extension
            else:
                # Handle binary files
                request = self.service.files().get_media(fileId=file_id)

            downloader = MediaIoBaseDownload(file, request)
            
            done = False
            last_progress = 0
            
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    if progress - last_progress >= 10:  # Update every 10%
                        print_color(f"Download progress: {progress}%", color="blue")
                        last_progress = progress

            if file.getvalue():
                # Create a downloads directory if it doesn't exist
                os.makedirs('downloads', exist_ok=True)
                file_path = os.path.join('downloads', file_name)
                
                # Check if file already exists and handle naming
                counter = 1
                base_name, extension = os.path.splitext(file_path)
                while os.path.exists(file_path):
                    file_path = f"{base_name}_{counter}{extension}"
                    counter += 1
                
                with open(file_path, 'wb') as f:
                    f.write(file.getvalue())
                print_color(f'\n✓ File downloaded successfully as: {file_path}', color="green")
                return file_name, file.getvalue()
            
            print_color("× No data received for download", color="red")
            return None, None

        except HttpError as error:
            if error.resp.status == 404:
                print_color(f"× File not found: {file_id}", color="red")
            elif error.resp.status == 403:
                print_color(f"× Access denied to file: {file_id}", color="red")
            else:
                print_color(f"× An error occurred while downloading: {str(error)}", color="red")
            return None, None
        except Exception as e:
            print_color(f"× Unexpected error while downloading: {str(e)}", color="red")
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

    def share_folder(self, folder_id, user_email, role='reader'):
        """Share a single folder with a user"""
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': user_email
            }
            
            result = self.service.permissions().create(
                fileId=folder_id,
                body=permission,
                sendNotificationEmail=False,
                fields='id'
            ).execute()
            
            if result and 'id' in result:
                print_color(f"✓ Shared folder {folder_id} with {user_email}", color="green")
                return True
                
        except Exception as e:
            print_color(f"× Error sharing folder {folder_id}: {str(e)}", color="red")
            return False

    def share_subfolders(self, parent_id, user_email, role='reader'):
        """Share all subfolders under a parent folder"""
        try:
            query = f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(
                q=query,
                fields='files(id, name)'
            ).execute()
            
            for folder in results.get('files', []):
                self.share_folder(folder['id'], user_email, role)
                # Recursively share subfolders
                self.share_subfolders(folder['id'], user_email, role)
                
        except Exception as e:
            print_color(f"× Error sharing subfolders of {parent_id}: {str(e)}", color="red")

    def share_folder_with_user(self, folder_id, target_email, notify=False):
        """Share a folder with a specific user. Reader permissions only 
        
        Args:
            folder_id (str): ID of the folder to share
            target_email (str): Email of the user to share with
            role (str, optional): Permission role. Defaults to 'writer'.
                                Can be 'reader', 'writer', or 'commenter'
            notify (bool, optional): Whether to send notification email. Defaults to False.
            
        Returns:
            bool: True if sharing was successful, False otherwise
        """
        try:
            permission = {
                'type': 'user',
                'role': "reader",
                'emailAddress': target_email
            }
            
            result = self.service.permissions().create(
                fileId=folder_id,
                body=permission,
                sendNotificationEmail=notify,
                fields='id'
            ).execute()
            
            if result and 'id' in result:
                print_color(f"✓ Shared folder {folder_id} with {target_email}", color="green")
                return True
                
        except HttpError as error:
            if error.resp.status == 404:
                print_color(f"× Folder {folder_id} not found", color="red")
            elif error.resp.status == 400:
                print_color(f"× Invalid sharing request for folder {folder_id}", color="red")
            elif error.resp.status == 403:
                print_color(f"× Permission denied for folder {folder_id}", color="red")
            else:
                print_color(f"× Error sharing folder {folder_id}: {str(error)}", color="red")
        except Exception as e:
            print_color(f"× Unexpected error sharing folder {folder_id}: {str(e)}", color="red")
            
        return False

    def share_all_folders(self, target_users, include_subfolders=True):
        """Share all accessible folders with target users as viewers"""
        try:
            folders = self.list_all_folders()
            for folder in folders:
                for user in target_users:
                    self.share_folder(
                        folder_id=folder['id'],
                        user_email=user,
                        role='reader'  # Changed from 'writer' to 'reader'
                    )
                    if include_subfolders:
                        self.share_subfolders(
                            parent_id=folder['id'],
                            user_email=user,
                            role='reader'  # Changed from 'writer' to 'reader'
                        )
        except Exception as e:
            print_color(f"Error sharing folders: {str(e)}", color="red")
            raise

    def get_folder_tree(self, folder_id='root', depth=None):
        """Get the folder structure as a tree
        
        Args:
            folder_id (str, optional): Starting folder ID. Defaults to 'root'
            depth (int, optional): Maximum depth to traverse. None for unlimited
            
        Returns:
            dict: Tree structure of folders
        """
        try:
            query = f"mimeType='application/vnd.google-apps.folder' and '{folder_id}' in parents"
            response = self.service.files().list(
                q=query,
                fields='files(id, name)'
            ).execute()
            
            folders = response.get('files', [])
            tree = {}
            
            # Base case for recursion
            if depth is not None and depth <= 0:
                return tree
                
            for folder in folders:
                new_depth = None if depth is None else depth - 1
                tree[folder['name']] = self.get_folder_tree(folder['id'], new_depth)
                
            return tree
            
        except HttpError as error:
            print_color(f"Error retrieving folder structure: {str(error)}", color="red")
            return {}

    def list_all_folders(self):
        """List all accessible folders in Drive"""
        try:
            query = "mimeType='application/vnd.google-apps.folder' and trashed=false"
            response = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            return response.get('files', [])
        except Exception as e:
            print_color(f"Error listing folders: {str(e)}", color="red")
            return []