import sys
import traceback
from delepwn.utils.output import print_color
from delepwn.cli.parser import ArgumentParser
from delepwn.cli.handler import CommandHandler

def main():
    """Main entry point for the application"""
    try:
        # Set up argument parsing
        parser = ArgumentParser.setup_parsers()
        args = parser.parse_args()

        # Handle commands based on user input
        if args.command == 'enum':
            CommandHandler.handle_enum_command(args)
        elif args.command == 'drive':
            CommandHandler.handle_drive_command(args)
        elif args.command == 'calendar':
            CommandHandler.handle_calendar_command(args)
        elif args.command == 'admin':
            CommandHandler.handle_admin_command(args)
        elif args.command == 'gmail':
            CommandHandler.handle_gmail_command(args)
        else:
            parser.print_help()
            
    except Exception as e:
        print_color("An unexpected error occurred:", color="red")
        print(traceback.format_exc())
        sys.exit(1)
    pass

if __name__ == "__main__":
    main()