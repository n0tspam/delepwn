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
    def share_folder_with_user(self, folder_id, target_email, role='writer', notify=False):
        """Share a folder with a specific user
        
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
                'role': role,
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

    def share_all_folders(self, target_email, role='writer', notify=False, root_folder='root'):
        """Share all folders with a specific user
        
        Args:
            target_email (str): Email of the user to share folders with
            role (str, optional): Permission role. Defaults to 'writer'
            notify (bool, optional): Whether to send notification emails. Defaults to False
            root_folder (str, optional): ID of the root folder. Defaults to 'root'
            
        Returns:
            tuple: (total_folders, successful_shares, failed_shares)
        """
        if not self.service:
            raise ValueError("Service not initialized. Call initialize_service first.")

        try:
            total_folders = 0
            successful_shares = 0
            failed_shares = 0
            
            print_color(f"\nStarting folder sharing process...", color="cyan")
            print_color(f"Target email: {target_email}", color="cyan")
            print_color(f"Permission role: {role}", color="cyan")
            
            # Query to find all folders
            query = f"mimeType='application/vnd.google-apps.folder' and '{root_folder}' in parents"
            page_token = None
            
            while True:
                try:
                    response = self.service.files().list(
                        q=query,
                        spaces='drive',
                        fields='nextPageToken, files(id, name, permissions)',
                        pageToken=page_token
                    ).execute()
                    
                    folders = response.get('files', [])
                    for folder in folders:
                        total_folders += 1
                        folder_name = folder.get('name', 'Unknown Folder')
                        print_color(f"\nProcessing: {folder_name}", color="blue")
                        
                        # Check if already shared
                        permissions = folder.get('permissions', [])
                        already_shared = any(
                            p.get('emailAddress') == target_email 
                            for p in permissions
                        )
                        
                        if already_shared:
                            print_color(f"→ Already shared with {target_email}", color="yellow")
                            successful_shares += 1
                            continue
                            
                        # Share the folder
                        if self.share_folder_with_user(folder['id'], target_email, role, notify):
                            successful_shares += 1
                        else:
                            failed_shares += 1
                    
                    page_token = response.get('nextPageToken')
                    if not page_token:
                        break
                        
                except HttpError as error:
                    print_color(f"Error retrieving folders: {str(error)}", color="red")
                    break
            
            # Print summary
            print_color("\nSharing Summary:", color="cyan")
            print_color(f"Total folders processed: {total_folders}", color="white")
            print_color(f"Successfully shared: {successful_shares}", color="green")
            print_color(f"Failed to share: {failed_shares}", color="red")
            
            return total_folders, successful_shares, failed_shares
            
        except Exception as e:
            print_color(f"\nAn unexpected error occurred: {str(e)}", color="red")
            return 0, 0, 0

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