import os 
import sys
from src.gcp_sa_enum import ServiceAccountEnumerator
from checkdelegation import CustomCredentials
from utils.text_color import print_color
import argparse

def check_gcp_bearer_access_token():
    token = os.environ.get('GCP_BEARER_ACCESS_TOKEN')
    if token:
        try:
            credentials = CustomCredentials(token)
            enumerator = ServiceAccountEnumerator(credentials, verbose=False)
            print_color(f"[+] GCP_BEARER_ACCESS_TOKEN is set with access token of {enumerator.user_email}", color="green")
        except HttpError as e:
            if e.resp.status == 401 and b"ACCESS_TOKEN_TYPE_UNSUPPORTED" in e.content:
                print("\nThe provided Bearer access token isn't valid. Refresh a new one.")
            else:
                print(f"An error occurred: {e}")

    else:
        print("GCP_BEARER_ACCESS_TOKEN is not set.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='GCP Service Account Enumerator')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.required = True  # Make the subparser required

    # Subparser for 'enum' command
    parser_enum = subparsers.add_parser('enum', help='Enumerate GCP Service Accounts')
    # If you have additional arguments for 'enum', add them here
    # parser_enum.add_argument('--verbose', action='store_true', help='Enable verbose output')

    # Subparser for 'drive' command
    drive_parser = subparsers.add_parser('drive', help='Impersonate a user and enumerate Google Drive.')

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

    if args.command == 'enum':
        print_color(f"[*] Beginning check for Domain-Wide delegation..\n", color="cyan")
        check_gcp_bearer_access_token()
    
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