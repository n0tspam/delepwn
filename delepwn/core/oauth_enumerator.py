from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.auth.exceptions import DefaultCredentialsError, RefreshError
from delepwn.core.domain_users import DomainUserEnumerator
from delepwn.utils.output import print_color
import requests
import os
from tqdm import tqdm


class OAuthEnumerator:
    """ Creates access token to each private key, OAuth scope, and distinct org email and validate whether they have DWD enabled"""
    def __init__(self, gcp_project_enumerator, scopes_file, key_folder, single_test_email, verbose=False):
        self.gcp_project_enumerator = gcp_project_enumerator
        self.scopes_file = scopes_file
        self.key_folder = key_folder
        self.scopes = self.read_scopes_from_file()
        self.valid_results = {}
        self.verbose = verbose
        self.confirmed_dwd_keys = []  # Keep track of keys with DWD
        self.user_emails = list(single_test_email.values())

    def get_valid_results(self):
        return self.valid_results

    def read_scopes_from_file(self):
        """ read OAuth scopes list and descriptions from oauth_scopes.txt"""
        try:
            scope_dict = {}
            with open(self.scopes_file, 'r') as file:
                content = file.readlines()
                for line in content:
                    line = line.strip()
                    if line and '|' in line:
                        scope, description = line.split('|', 1)
                        scope = scope.strip()
                        description = description.strip()
                        scope_dict[scope] = description
            return scope_dict
            
        except FileNotFoundError:
            print_color(f"Error: Scopes file not found at: {self.scopes_file}", color="red")
            return {}
        except Exception as e:
            print_color(f"Error reading scopes file: {str(e)}", color="red")
            return {}

    def get_org_emails(self):
        domain_user_enumerator = DomainUserEnumerator(self.gcp_project_enumerator)
        unique_users = domain_user_enumerator.list_unique_domain_users()
        return list(unique_users.values())

    def jwt_creator(self):
        """ Create JWT objects for each combination of workspace distinct org email, OAuth scope, and private key pair  """
        jwt_objects = []
        for json_file in os.listdir(self.key_folder):
            json_path = os.path.join(self.key_folder, json_file)

            for user_email in self.user_emails:
                for scope in self.scopes.keys():  # Use keys() since scopes is now a dictionary
                    creds = service_account.Credentials.from_service_account_file(
                        json_path,
                        scopes=[scope],
                    )
                    creds = creds.with_subject(user_email)
                    jwt_objects.append((json_path, user_email, scope, creds))
        return jwt_objects

    def print_valid_output(self):
        """Print OAuth enumeration results in a standardized format"""
        for token, scopes in self.valid_results.items():
            print_color("\nDomain-Wide Delegation Results", color="cyan")
            print_color("-" * 50, color="blue")
            print_color(f"Service Account enabled for DWD: {token}", color="white")
            
            print_color("\nAuthorized Scopes:", color="cyan")
            print_color("-" * 50, color="blue")
            
            for scope in scopes:
                print_color(f"-> {scope}", color="yellow")
                description = self.scopes.get(scope)
                if description:
                    print_color(f"   {description}", color="white")
            
            print_color("-" * 50, color="blue")

    def token_validator(self, jwt_objects):
        """ Validate access tokens for each JWT object combination  """
        total = len(jwt_objects)
        
        print_color("\nValidating OAuth tokens and DWD access:", color="cyan")
        print_color("-" * 50, color="blue")
        print_color(f"Total combinations to check: {total}", color="white")
        print_color(f"Service Accounts: {len(os.listdir(self.key_folder))}", color="white")
        print_color(f"OAuth Scopes: {len(self.scopes)}", color="white")
        print_color(f"Target Users: {len(self.user_emails)}", color="white")
        print_color("-" * 50, color="blue")

        with tqdm(total=total, desc="Progress", unit="token") as pbar:
            for json_path, user_email, scope, creds in jwt_objects:
                try:
                    creds.refresh(Request())
                    token_info_url = f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={creds.token}"
                    response = requests.get(token_info_url)

                    if response.status_code == 200:
                        self.valid_results.setdefault(json_path, []).append(scope)
                        if json_path not in self.confirmed_dwd_keys:
                            self.confirmed_dwd_keys.append(json_path)
                            if self.verbose:
                                tqdm.write(f"-> Found valid DWD access with scope: {scope}")

                except DefaultCredentialsError:
                    if self.verbose:
                        tqdm.write("The service account file is not valid or doesn't exist.")
                except RefreshError as e:
                    if self.verbose:
                        tqdm.write(f"-> Invalid or expired token with scope {scope}")
                except Exception as e:
                    if self.verbose:
                        tqdm.write(f"-> Error validating token: {str(e)}")
                finally:
                    pbar.update(1)

        if self.valid_results:
            print_color("\nResults Summary:", color="cyan")
            self.print_valid_output()
        else:
            print_color("\nNo valid DWD access found", color="yellow")

    def total_jwt_combinations(self):
        """ calculate total combinations of JWT based on the number of enumerated OAuth scopes, GCP private keys pairs and target workspace org emails
        (oauth_scopes.txt number * private key pairs * target workspace org (distinct) emails)"""
        num_scopes = len(self.scopes)
        num_keys = len(os.listdir(self.key_folder))
        num_emails = len(self.user_emails)
        return num_scopes * num_keys * num_emails

    def run(self):
        """Main execution method"""
        if not os.path.exists(self.scopes_file):
            print_color(f"[!] Scopes file not found at: {self.scopes_file}", color="red")
            return
        
        if not self.scopes or len(self.scopes) == 0:
            print_color('[!] No scopes loaded from scopes file. Exiting.', color="yellow")
            if self.verbose:
                print_color(f"Scopes file location: {self.scopes_file}", color="blue")
            return

        if not os.path.exists(self.key_folder) or not os.listdir(self.key_folder):
            print_color("[!] No GCP private key pairs were found. It might suggest the IAM user doesn't have permission to create keys on target Service Accounts. Try to use different GCP identity", color="red")
            return

        total_combinations = self.total_jwt_combinations()
        if self.verbose:
            print_color(f"Total scope combinations to test: {total_combinations}", color="blue")
            print_color(f"Number of scopes: {len(self.scopes)}", color="blue")
            print_color(f"Number of keys: {len(os.listdir(self.key_folder))}", color="blue")
            print_color(f"Number of users: {len(self.user_emails)}", color="blue")

        jwt_objects = self.jwt_creator()
        self.token_validator(jwt_objects)
