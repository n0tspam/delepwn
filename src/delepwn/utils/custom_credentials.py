from google.auth.credentials import Credentials

class CustomCredentials(Credentials):
    """Custom credentials class that supports both token and service account authentication"""

    def __init__(self, token=None, service_account_credentials=None):
        super().__init__()
        self.token = token
        self.sa_credentials = service_account_credentials
        
    def apply(self, headers):
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        elif self.sa_credentials:
            # Let the service account credentials handle authorization
            self.sa_credentials.apply(headers)
        
    def before_request(self, request, method, url, headers):
        self.apply(headers)
        
    def refresh(self, request):
        if self.sa_credentials:
            self.sa_credentials.refresh(request)
        # Token-based credentials don't need refresh
        pass

    @property
    def service_account_email(self):
        """Return service account email if using SA credentials"""
        if self.sa_credentials:
            return self.sa_credentials.service_account_email
        return None 