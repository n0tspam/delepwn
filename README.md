# DelePwn

DelePwn is a security assessment tool designed to identify and demonstrate the risks associated with Google Workspace Domain-Wide Delegation (DWD) misconfigurations in Google Cloud Platform (GCP) environments. This tool helps security professionals and administrators evaluate their organization's exposure to potential DWD-based attacks.

## What is Domain-Wide Delegation?
Domain-Wide Delegation (DWD) is a Google Workspace feature that allows service accounts to impersonate any user within a domain and access their Google Workspace data through Google APIs. While this feature is powerful for automation and service integrations, misconfigurations can lead to significant security risks. An attacker who gains access to a service account with DWD could potentially access any user's Gmail, Drive, Calendar, and other Google Workspace services, making it a critical security control that requires careful management.

## Features

### Feature Overview

| Module | Command | Capabilities | Description |
|--------|---------|--------------|-------------|
| [Enumeration](#1-enumeration-enum) | `enum` | `--verbose`<br>`--email`<br>`--output` | • Discovers GCP service accounts with DWD<br>• Maps service accounts to domain users<br>• Validates OAuth scopes<br>• Generates detailed reports |
| [Drive Operations](#2-google-drive-operations-drive) | `drive` | `--list`<br>`--download`<br>`--sharefolders`<br>`--folder` | • Lists Drive contents<br>• Downloads files<br>• Recursive folder sharing<br>• Exports Google Workspace files |
| [Calendar Management](#3-calendar-management-calendar) | `calendar` | `--list`<br>`--details`<br>`--create`<br>`--delete` | • Manages calendar events<br>• Creates events from YAML<br>• Google Meet integration<br>• Event notifications handling |
| [Admin Operations](#4-admin-operations-admin) | `admin` | `--elevate`<br>`--create` | • Creates admin users<br>• Elevates user privileges<br>• Manages admin access<br>• Permission validation |

### 1. Enumeration (`enum`)
- Discovers GCP service accounts with DWD privileges
- Enumerates OAuth scopes for identified service accounts
- Maps service accounts to domain users
- Validates DWD configurations across discovered accounts
- Supports verbose output mode for detailed analysis
- Optional output to formatted results file

### 2. Google Drive Operations (`drive`)
- Lists all contents of Google Drive
- Downloads specific files using file IDs
- Lists files within specific folders
- Shares folders with specified target emails
- Supports recursive folder sharing
- Exports Google Workspace files in appropriate formats

### 3. Calendar Management (`calendar`)
- Lists calendar events within specified date ranges
- Creates calendar events from YAML configurations
- Retrieves detailed event information
- Deletes calendar events
- Supports Google Meet integration
- Manages event notifications and reminders

### 4. Admin Operations (`admin`)
- Creates new admin users in Google Workspace
- Elevates existing users to admin status
- Manages user privileges
- Validates admin operations and permissions

## Installation

Using poetry (recommended):
```bash
# Clone the repository
git clone https://github.com/yourusername/delepwn.git
cd delepwn

# Install with poetry
poetry install

# Run delepwn
poetry run delepwn [command] [options]
```

Using pip:
```bash
# Install from the repository
pip install .

# Run delepwn
delepwn [command] [options]
```

### Environment Setup

Before running any commands, make sure to set up your GCP Bearer Access Token:

```bash
export GCP_BEARER_ACCESS_TOKEN="your_token_here"  # Linux/MacOS
set GCP_BEARER_ACCESS_TOKEN=your_token_here       # Windows CMD
$env:GCP_BEARER_ACCESS_TOKEN="your_token_here"    # Windows PowerShell
```


## Requirements

- Python 3.8 or higher
- Poetry package manager
- Valid GCP Bearer Access Token for a user with `iam.serviceAccountKeys.create` permission

## Usage

### Basic Commands

1. Enumeration:
```bash
# Using poetry
poetry run delepwn enum [--verbose] [--email EMAIL] [--output]

# Using direct installation
delepwn enum [--verbose] [--email EMAIL] [--output]
```

2. Drive Operations:
```bash
# List files
poetry run delepwn drive --key-file KEY_FILE --impersonate EMAIL --list [--output OUTPUT_FILE]

# Download specific file
poetry run delepwn drive --key-file KEY_FILE --impersonate EMAIL --download FILE_ID

# Share folders
poetry run delepwn drive --key-file KEY_FILE --impersonate EMAIL --sharefolders TARGET_EMAIL
```

3. Calendar Operations:
```bash
# List events
poetry run delepwn calendar --key-file KEY_FILE --impersonate EMAIL --list --start-date YYYY-MM-DD --end-date YYYY-MM-DD

# Get event details
poetry run delepwn calendar --key-file KEY_FILE --impersonate EMAIL --details EVENT_ID

# Create event from config
poetry run delepwn calendar --key-file KEY_FILE --impersonate EMAIL --create CONFIG_FILE

# Delete event
poetry run delepwn calendar --key-file KEY_FILE --impersonate EMAIL --delete EVENT_ID
```

4. Admin Operations:
```bash
# Elevate user to admin
poetry run delepwn admin --key-file KEY_FILE --impersonate EMAIL --elevate TARGET_EMAIL

# Create new admin user
poetry run delepwn admin --key-file KEY_FILE --impersonate EMAIL --create NEW_ADMIN_EMAIL
```

Note: If you installed the package with pip, you can replace `poetry run delepwn` with just `delepwn` in all the above commands.



### Example Calendar Configuration

When using the `calendar --create <config file>` feature, you can specify the appropriate data in a `.yaml` file and pass the path as an argument to the program. You can view the `examples/example_calendarphish.yaml` file included in this repo as a starting point.

```yaml
event:
  summary: "Meeting Title"
  description: "Meeting Description"
  start_time: "2024-12-01T10:00:00-05:00"
  end_time: "2024-12-01T10:30:00-05:00"
  timezone: "America/New_York"
  attendees:
    - "user1@domain.com"
    - "user2@domain.com"
```

## Future Work

1. Enhanced Features:
   - Support for additional Google Workspace services
   - Integration with other cloud platforms
   - Advanced reporting capabilities
   - Automated remediation suggestions

2. Technical Improvements:
   - Async operations support
   - Rate limiting and throttling
   - Enhanced error handling
   - Expanded logging capabilities

3. Security Enhancements:
   - Implementation of additional security controls
   - Support for custom security policies
   - Enhanced credential management
   - Audit logging improvements

4. User Experience:
   - Interactive CLI mode
   - Web interface development
   - Better progress indicators
   - Enhanced documentation

## References / Acknowledgements

Special shoutout to the developers of (https://github.com/axon-git/DeleFriend)[https://github.com/axon-git/DeleFriend]. They have an incredible explanation of how DWD privileges can be enumerated in their repo. Pretty much all of the code from the `enum` function is based on their research and work, so thank you! 

The implementation of the `admin` function was based on [gcp_delegation.py](https://gitlab.com/gitlab-com/gl-security/security-operations/redteam/redteam-public/pocs/gcp_misc/-/blob/master/gcp_delegation.py) so also a shoutout to them!


## Disclaimer

This tool is intended for security research and legitimate testing purposes only. Users are responsible for obtaining appropriate authorization before conducting any security assessments. The authors are not responsible for misuse or damages resulting from the use of this tool.
