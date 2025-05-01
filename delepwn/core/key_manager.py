import os
import json
import base64
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from delepwn.utils.output import print_color
from delepwn.config.settings import SERVICE_ACCOUNT_KEY_FOLDER


class PrivateKeyCreator:
    """ Creates GCP private key pairs for SAs with permissions """
    def __init__(self, credentials):
        self.credentials = credentials
        self.iam_service = build('iam', 'v1', credentials=self.credentials)
        self.keys_directory = SERVICE_ACCOUNT_KEY_FOLDER
        os.makedirs(self.keys_directory, exist_ok=True)
    
    def check_existing_key(self, service_account_path):
        """Check if a valid key already exists for this service account"""
        sa_email = service_account_path.split('/')[-1]
        for key_file in os.listdir(self.keys_directory):
            file_path = os.path.join(self.keys_directory, key_file)
            try:
                # Use a context manager for proper file handling
                with open(file_path, 'r') as f:
                    try:
                        key_data = json.load(f)
                        if key_data.get('client_email') == sa_email:
                            # Validate the key still works
                            try:
                                creds = service_account.Credentials.from_service_account_info(
                                    key_data,
                                    scopes=['https://www.googleapis.com/auth/cloud-platform.read-only']
                                )
                                creds.refresh(Request())
                                print_color(f"  Using existing valid key for {sa_email} at {file_path}\n", color="blue")
                                return True
                            except Exception as e:
                                print_color(f"  Found existing key for {sa_email} but it's invalid ({str(e)}), creating new one.", color="blue")
                                # Make sure file is closed before trying to remove it
                                try:
                                    f.close()  # Ensure the file is closed
                                    os.remove(file_path)
                                except OSError as ose:
                                    print_color(f"[!] Could not remove invalid key file: {str(ose)}", color="yellow")
                    except json.JSONDecodeError:
                        print_color(f"[!] Invalid JSON in key file {file_path}", color="red")
            except Exception as e:
                print_color(f"[!] Error checking existing key {file_path}: {str(e)}", color="red")
                continue
        return False

    def create_service_account_key(self, service_account_path):
        # Check for existing valid key first
        if self.check_existing_key(service_account_path):
            return

        try:
            key = self.iam_service.projects().serviceAccounts().keys().create(
                name=service_account_path,
                body={
                    "keyAlgorithm": "KEY_ALG_RSA_2048",
                    "privateKeyType": "TYPE_GOOGLE_CREDENTIALS_FILE",
                }
            ).execute()

            # The private key data is a base64-encoded JSON string within the attr privateKeyData
            key_json = base64.b64decode(key['privateKeyData']).decode('utf-8')
            key_data = json.loads(key_json)

            file_name = service_account_path.replace('/', '_').replace(':', '_')
            file_path = os.path.join(self.keys_directory, f"{file_name}.json")
            with open(file_path, "w") as file:
                json.dump(key_data, file)  # Save the decoded key data, not the entire key object

            print_color(f"\n[*] Key created and saved to {file_path}", color="blue")

        except Exception as e:
            if "Precondition check failed." in str(e):
                # extracting the service account name from the full service account path
                sa_name = service_account_path.split('/')[-1]
                print_color(
                    f"[!] Issues with creating a private key for {sa_name}. Validate the number of existing key pairs isn't more than 10", color="red")
            else:
                print_color(f"[!] An error occurred while creating service account key: {e}", color="red")

    def delete_remote_key(self, key_name):
        """ Delete the remote service account key """
        try:
            self.iam_service.projects().serviceAccounts().keys().delete(name=key_name).execute()
            print_color(f"✓ Successfully deleted remote service account key: {key_name}", color="green")
        except Exception as e:
            print_color(f"[!] Error deleting remote key {key_name}: {e}", color="red")

    def delete_keys_without_dwd(self, confirmed_dwd_keys):
        """Delete service account keys that don't have DWD enabled, keep the ones that do"""
        print_color("\nCleaning Up Service Account Keys", color="cyan")
        print_color("-" * 50, color="blue")
        
        try:
            # Get list of all key files
            key_files = os.listdir(self.keys_directory)
            
            # Convert confirmed_dwd_keys to just filenames
            dwd_filenames = [os.path.basename(path) for path in confirmed_dwd_keys]
            
            # Track statistics
            total_keys = len(key_files)
            dwd_keys = 0
            deleted_keys = 0
            
            for key_file in key_files:
                key_path = os.path.join(self.keys_directory, key_file)
                
                # If key has DWD enabled, keep it
                if key_file in dwd_filenames:
                    dwd_keys += 1
                    print_color(f"-> Keeping key with DWD access: {key_file}", color="white")
                    continue
                    
                try:
                    # Read the key file to get the key ID
                    with open(key_path, 'r') as f:
                        key_data = json.load(f)
                        
                    # Delete the remote key
                    key_id = key_data.get('private_key_id')
                    project_id = key_data.get('project_id')
                    client_email = key_data.get('client_email')
                    
                    if key_id and project_id and client_email:
                        # Format the key name according to the required pattern
                        full_key_name = f"projects/{project_id}/serviceAccounts/{client_email}/keys/{key_id}"
                        self.iam_service.projects().serviceAccounts().keys().delete(
                            name=full_key_name
                        ).execute()
                        print_color(f"-> Removed remote key: {full_key_name}", color="white")
                    
                    # Delete the local key file
                    os.remove(key_path)
                    print_color(f"-> Removed local key: {key_file}", color="white")
                    deleted_keys += 1
                    
                except Exception as e:
                    print_color(f"-> Failed to remove key {key_file}: {str(e)}", color="red")
                    
            # Print summary
            print_color("-" * 50, color="blue")
            print_color("Key Cleanup Summary:", color="cyan")
            print_color(f"Total keys processed: {total_keys}", color="white")
            print_color(f"Keys with DWD access: {dwd_keys}", color="white")
            print_color(f"Keys removed: {deleted_keys}", color="white")
            print_color("-" * 50, color="blue")
            
        except Exception as e:
            print_color(f"Error during key cleanup: {str(e)}", color="red")