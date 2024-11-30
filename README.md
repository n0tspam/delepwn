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

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DelePwn.git
cd DelePwn
```

2. Install dependencies using Poetry:
```bash
poetry install
```

## Requirements

- Python 3.7 or higher
- Poetry package manager
- GCP Service Account with appropriate permissions
- Valid GCP Bearer Access Token

## Usage

### Basic Commands

1. Enumeration:
```
python main.py enum [--verbose] [--email EMAIL] [--output]
```

2. Drive Operations:
```
python main.py drive --key-file KEY_FILE --impersonate EMAIL [--list | --download FILE_ID | --sharefolders TARGET_EMAIL]
```

3. Calendar Operations:
```
python main.py calendar --key-file KEY_FILE --impersonate EMAIL [--list | --details EVENT_ID | --create CONFIG_FILE | --delete EVENT_ID]
```

4. Admin Operations:
```
python main.py admin --key-file KEY_FILE --impersonate EMAIL [--elevate TARGET_EMAIL | --create NEW_ADMIN_EMAIL]
```

### Example Calendar Configuration

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

## Security Considerations

- This tool is intended for legitimate security assessment purposes only
- Always obtain proper authorization before testing
- Follow responsible disclosure practices
- Be aware of applicable laws and regulations
- Handle sensitive data appropriately

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

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Submit a pull request

## Acknowledgements



## Disclaimer

This tool is intended for security research and legitimate testing purposes only. Users are responsible for obtaining appropriate authorization before conducting any security assessments. The authors are not responsible for misuse or damages resulting from the use of this tool.

## License

MIT License

Copyright (c) [2024] [n0tspam]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
