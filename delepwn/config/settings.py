"""Global configuration settings"""

import os
from pathlib import Path

# Get the project root directory (parent of delepwn folder)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Base paths
KEYS_DIR = os.path.join(PROJECT_ROOT, "SA_private_keys")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
DOWNLOADS_DIR = os.path.join(PROJECT_ROOT, "downloads")
EXAMPLES_DIR = os.path.join(PROJECT_ROOT, "examples")

# OAuth scopes file
OAUTH_SCOPES_FILE = 'delepwn/config/oauth_scopes.txt'

# Ensure required directories exist
for directory in [KEYS_DIR, RESULTS_DIR, DOWNLOADS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Service settings
DRIVE_API_VERSION = "v3"
CALENDAR_API_VERSION = "v3"
IAM_API_VERSION = "v1"

# OAuth scopes
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive']
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']
IAM_SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

# Environment variables
GCP_TOKEN_ENV_VAR = "GCP_BEARER_ACCESS_TOKEN"

# Rate limiting settings
MAX_API_RETRIES = 5
RATE_LIMIT_BACKOFF_FACTOR = 2
API_RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

# File paths
SERVICE_ACCOUNT_KEY_FOLDER = KEYS_DIR
RESULTS_FOLDER = RESULTS_DIR

# API settings
API_RETRY_COUNT = 3
API_RETRY_DELAY = 1  # seconds

# Default timeouts
DEFAULT_REQUEST_TIMEOUT = 30  # seconds