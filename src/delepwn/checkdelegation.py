import yaml
import argparse
from google.auth.credentials import Credentials
from delepwn.gcp_sa_enum import ServiceAccountEnumerator
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from delepwn import oauth_scope_enumerator
from delepwn.domain_users_enum import DomainUserEnumerator
import os
import traceback
from datetime import datetime
from delepwn.utils.text_color import print_color

SCOPES_FILE = 'src/delepwn/oauth_scopes.txt'  #  scopes file
KEY_FOLDER = 'SA_private_keys'


class CustomCredentials(Credentials):

    def __init__(self, token):
        self.token = token

    def apply(self, headers):
        headers['Authorization'] = f'Bearer {self.token}'

    def before_request(self, request, method, url, headers):
        self.apply(headers)

    def refresh(self, request):
        pass


def results(oauth_enumerator):
    """
    Write enumeration results to a file in the results directory
    Args:
        oauth_enumerator: The OAuthEnumerator instance containing results
    """
    # Create results directory if it doesn't exist
    result_folder = 'results'
    os.makedirs(result_folder, exist_ok=True)

    # Generate filename with datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"delepwn_enum_{timestamp}.txt"
    filepath = os.path.join(result_folder, filename)

    valid_results = oauth_enumerator.get_valid_results()
    
    if not valid_results:
        print("\n[!] No valid results found to save.")

    with open(filepath, 'w') as f:
        # Write header
        f.write("=" * 50 + "\n")
        f.write("DelePwn Enum Scan Results\n")
        f.write(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")

        # Write results for each service account
        for json_path, valid_scopes in valid_results.items():
            if valid_scopes:
                # Service Account section
                f.write("-" * 40 + "\n")
                f.write(f"Service Account: {os.path.basename(json_path)}\n")
                f.write("-" * 40 + "\n")
                
                # OAuth Scopes section
                f.write("\nValid OAuth Scopes:\n")
                for scope in valid_scopes:
                    f.write(f"  • {scope}\n")
                f.write("\n")
    print_color(f"\n[+] Results saved to {filepath}", color="blue")

    return filepath



def check(enumerator, testEmail, verbose, enum_output):
    try:
        print_color(f"\n→ Enumerating GCP Resources: Projects and Service Accounts...\n", color="cyan")
        enumerator.enumerate_service_accounts()

        if testEmail:
            print_color(f"\n[*] Using provided test email: {testEmail}", color="white")
            # Create a dictionary with the test email in the same format as single_test_email
            domain = testEmail.split('@')[1]
            test_email_dict = {domain: testEmail}
            oauth_enumerator = oauth_scope_enumerator.OAuthEnumerator(enumerator, SCOPES_FILE, KEY_FOLDER, test_email_dict, verbose=verbose)
        else:
            # If no test email provided, enumerate users to find one
            domain_user_enumerator = DomainUserEnumerator(enumerator)
            domain_user_enumerator.print_unique_domain_users()
            oauth_enumerator = oauth_scope_enumerator.OAuthEnumerator(enumerator, SCOPES_FILE, KEY_FOLDER, domain_user_enumerator.single_test_email, verbose=verbose)

        print_color("\n[*] Enumerating OAuth scopes and private key access tokens... (it might take a while based on the number of the JWT combinations)\n", color="yellow")
        oauth_enumerator.run()
        confirmed_dwd_keys = oauth_enumerator.confirmed_dwd_keys
        enumerator.key_creator.delete_keys_without_dwd(confirmed_dwd_keys)

        if enum_output:
            results(oauth_enumerator)
    except Exception as e:
        print_color(f"An error occurred: {e}", color="red")
        traceback.print_exc()