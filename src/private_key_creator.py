import os
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from utils.text_color import print_color
import base64

class PrivateKeyCreator:
    """ Creates GCP private key pairs for SAs with permissions """
    def __init__(self, credentials):
        self.credentials = credentials
        self.iam_service = build('iam', 'v1', credentials=self.credentials)
        self.keys_directory = "SA_private_keys"
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
                                print_color(f"[*] Using existing valid key for {sa_email} at {file_path}", color="cyan")
                                return True
                            except Exception as e:
                                print_color(f"[!] Found existing key for {sa_email} but it's invalid ({str(e)}), creating new one.", color="yellow")
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

            print_color(f"\n[*] Key created and saved to {file_path}", color="cyan")

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
            print_color(f"[+] Successfully deleted remote service account key: {key_name}", color="green")
        except Exception as e:
            print_color(f"[!] Error deleting remote key {key_name}: {e}", color="red")

    def delete_keys_without_dwd(self, confirmed_dwd_keys):
        """ Delete SA keys which found without DWD from local folder and remotely"""
        print_color("\n[*] Clearing private keys without DWD enabled ...", color="cyan")
        for key_path in os.listdir(self.keys_directory):
            full_path = os.path.join(self.keys_directory, key_path)
            if full_path not in confirmed_dwd_keys:
                try:
                    # Delete the key remotely
                    with open(full_path, 'r') as key_file:
                        key_data = json.load(key_file)
                        client_email = key_data["client_email"]
                        key_id = key_data["private_key_id"]
                        project_id = key_data["project_id"]
                        # API is expecting the following format projects/{PROJECT_ID}/serviceAccounts/{SERVICE_ACCOUNT_EMAIL}/keys/{KEY_ID}
                        resource_name = f"projects/{project_id}/serviceAccounts/{client_email}/keys/{key_id}"
                        self.delete_remote_key(resource_name)
                    # Delete the key locally
                    os.remove(full_path)
                    print_color(f"[+] Deleted local service account key without DWD: {full_path}", color="green")
                except OSError as e:
                    print_color(f"Error deleting {full_path}: {e}", color="red")