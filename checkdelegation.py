import yaml
import argparse
from google.auth.credentials import Credentials
from src.gcp_sa_enum import ServiceAccountEnumerator
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from src import oauth_scope_enumerator
from src.domain_users_enum import DomainUserEnumerator
import os
import traceback
import time
from utils.text_color import print_color

SCOPES_FILE = 'src/oauth_scopes.txt'  #  scopes file
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
    timestamp = int(time.time())
    result_folder = 'results'
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)

    filename = f'results_{timestamp}.txt'
    filepath = os.path.join(result_folder, filename)
    print_color(f"\n✓ Saving results to results/{filename}\n", color="green")

    with open(filepath, 'w') as f:
        valid_results = oauth_enumerator.get_valid_results()
        for json_path, valid_scopes in valid_results.items():
            if valid_scopes:
                f.write(f'Service Account Key Name: {os.path.basename(json_path)}\n')
                f.write('Valid OAuth Scopes:\n')
                for scope in valid_scopes:
                    f.write(f'{scope}\n')
                f.write('---\n')



def check(enumerator, testEmail, verbose):
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

        results(oauth_enumerator)
    except Exception as e:
        print_color(f"An error occurred: {e}", color="red")
        traceback.print_exc()