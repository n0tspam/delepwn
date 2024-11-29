
import os
import sys
import csv
from datetime import datetime, timedelta
from src.gcp_sa_enum import ServiceAccountEnumerator
from checkdelegation import CustomCredentials, check
from utils.text_color import print_color
from drive_manager import DriveManager
from calendar_manager import CalendarManager

class CommandHandler:
    """Handles command execution for different modules"""
    
    @staticmethod
    def handle_enum_command(args):
        """Handle enumeration commands"""
        token = os.environ.get('GCP_BEARER_ACCESS_TOKEN')
        if not token:
            print_color("GCP_BEARER_ACCESS_TOKEN environment variable is not set. This tool requires an access token for "
                       "a user with the iam.ServiceAccountKeys.create permission.", color="red")
            sys.exit(1)

        try:
            credentials = CustomCredentials(token)
            enumerator = ServiceAccountEnumerator(credentials, verbose=args.verbose)
            if enumerator.user_email is None:
                raise Exception(print_color("[-] Error verifying token. Ensure it's refreshed.", color="red"))
            print_color(f"✓ GCP_BEARER_ACCESS_TOKEN is set with access token of {enumerator.user_email}", color="green")
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
        """Handle drive share subcommand"""
        print_color(f"\nStarting folder sharing process...", color="cyan")
        drive_manager.share_all_folders(
            target_email=args.sharefolders,
            role='writer'
        )

    @staticmethod
    def handle_calendar_command(args):
        """Handle calendar-related commands"""
        try:
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