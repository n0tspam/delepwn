# argument_parser.py

import argparse

class ArgumentParser:
    """Handles command line argument parsing"""
    
    @staticmethod
    def setup_parsers():
        """Set up all command line argument parsers
        
        Returns:
            argparse.ArgumentParser: Configured argument parser
        """
        parser = argparse.ArgumentParser(description='Exploit Domain-Wide Delegation in GCP')
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        subparsers.required = True

        ArgumentParser._setup_enum_parser(subparsers)
        ArgumentParser._setup_drive_parser(subparsers)
        ArgumentParser._setup_calendar_parser(subparsers)

        return parser

    @staticmethod
    def _setup_enum_parser(subparsers):
        """Set up enum command parser"""
        parser_enum = subparsers.add_parser('enum', 
            help='Enumerate GCP service accounts with DWD privileges.')
        parser_enum.add_argument('--verbose', action='store_true', default=False,
            help='Enable verbose output')
        parser_enum.add_argument('--email', type=str,
            help='Optional: Specify a single email to test DWD against instead of enumerating users')    
        parser_enum.add_argument('--output', action='store_true', default=False,
            help='Enable colored, formatted output in results.txt file')

    @staticmethod
    def _setup_drive_parser(subparsers):
        """Set up drive command parser"""
        drive_parser = subparsers.add_parser('drive',
            help='Impersonate a user and perform actions on Google Drive.')
        
        # Required arguments
        drive_parser.add_argument('--key-file', type=str, required=True,
            help='Path to service account JSON key file')
        drive_parser.add_argument('--impersonate', type=str, required=True,
            help='User to impersonate')
            
        # Optional arguments
        drive_parser.add_argument('--output', type=str,
            help='Output CSV file for file listing')
        drive_parser.add_argument('--folder', type=str,
            help='List files in specific folder')
            
        # Mutually exclusive command group
        group = drive_parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--download', type=str, metavar='FILE_ID',
            help='Download a file from Google Drive')
        group.add_argument('--list', action='store_true',
            help='List all contents of Google Drive')
        group.add_argument('--sharefolders', type=str, metavar='TARGET_EMAIL',
            help='Share all folders with the specified target email')

    @staticmethod
    def _setup_calendar_parser(subparsers):
        """Set up calendar command parser"""
        calendar_parser = subparsers.add_parser('calendar',
            help='Impersonate a user and perform actions on Google Calendar.')
            
        # Required arguments
        calendar_parser.add_argument('--key-file', type=str, required=True,
            help='Path to service account JSON key file')
        calendar_parser.add_argument('--impersonate', type=str, required=True,
            help='User to impersonate')
        
        # Mutually exclusive command group
        calendar_group = calendar_parser.add_mutually_exclusive_group(required=True)
        calendar_group.add_argument('--list', action='store_true',
            help='List calendar events (requires --start-date and --end-date)')
        calendar_group.add_argument('--details', type=str, metavar='EVENT_ID',
            help='Get detailed information about a specific event')
        calendar_group.add_argument('--delete', type=str, metavar='EVENT_ID',
            help='Delete a calendar event')
        calendar_group.add_argument('--create', type=str, metavar='CONFIG_FILE',
            help='Create event using YAML configuration file')
        
        # Date range arguments
        date_group = calendar_parser.add_argument_group('date range arguments')
        date_group.add_argument('--start-date', type=str,
            help='Start date for listing events (YYYY-MM-DD format)')
        date_group.add_argument('--end-date', type=str,
            help='End date for listing events (YYYY-MM-DD format)')

        # Custom validation to require both dates when using --list
        def validate_args(args):
            if args.list and not (args.start_date and args.end_date):
                calendar_parser.error('--list requires both --start-date and --end-date')
            return args

        # Override the default parse_args
        calendar_parser.parse_args = lambda: validate_args(argparse.ArgumentParser.parse_args(calendar_parser))