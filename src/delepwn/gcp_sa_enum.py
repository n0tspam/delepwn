import requests
from googleapiclient.discovery import build
from delepwn.private_key_creator import PrivateKeyCreator
from delepwn.utils.text_color import print_color
from delepwn.utils.api_utils import handle_api_ratelimit
from delepwn.utils.custom_credentials import CustomCredentials

class ServiceAccountEnumerator:
    """Enumerate GCP Projects and Service Accounts and find roles with iam.serviceAccountKeys.create permission"""
    def __init__(self, credentials, verbose=False, project_id=None):
        self.credentials = credentials
        self.resource_manager_service = build('cloudresourcemanager', 'v1', credentials=self.credentials)
        self.iam_service = build('iam', 'v1', credentials=self.credentials)
        
        # Handle both CustomCredentials and direct service account credentials
        if isinstance(credentials, CustomCredentials):
            self.user_email = (self.get_iam_email_from_token() 
                              if credentials.token 
                              else credentials.service_account_email)
        else:
            # Direct service account credentials
            self.user_email = credentials.service_account_email
        
        self.key_creator = PrivateKeyCreator(credentials)
        self.verbose = verbose
        self.project_id = project_id

    def get_iam_email_from_token(self):
        """Get the email associated with the access token"""
        try:
            response = requests.get(
                'https://www.googleapis.com/oauth2/v1/tokeninfo?alt=json',
                headers={'Authorization': f'Bearer {self.credentials.token}'}
            )
            response.raise_for_status()
            token_info = response.json()
            # Service Account access tokens return different token parameters
            if 'email' not in token_info:
                azp = token_info.get('issued_to')
                return self.find_service_account_email_by_client_id(azp) if azp else None
            return response.json().get('email')
        except requests.RequestException as e:
            print_color(f"Error fetching user info: {e}", color="red")
            return None

    def find_service_account_email_by_client_id(self, client_id):
        """Find the target service account email by matching the oauth2ClientId and azp values. This function relevant only for SA access tokens"""
        for project_id in self.get_projects():
            request = self.iam_service.projects().serviceAccounts().list(
                name='projects/' + project_id,
            )
            response = request.execute()
            if 'accounts' in response:
                for account in response['accounts']:
                    sa_details = self.get_service_account_details(account['name'])
                    if sa_details and sa_details.get('oauth2ClientId') == client_id:
                        return account['email']
        return None

    @handle_api_ratelimit
    def get_service_account_details(self, service_account_name):
        """Get detailed information about the service account, including the oauth2ClientId. This function relevant only for SA access tokens"""
        request = self.iam_service.projects().serviceAccounts().get(name=service_account_name)
        try:
            response = request.execute()
            return response
        except Exception as e:
            print(f"Error retrieving service account details: {e}")
            return None

    def get_service_account_roles(self, service_account):
        """Get the roles on the target Service Account resources from the IAM Policy"""
        request = self.iam_service.projects().serviceAccounts().getIamPolicy(  # Get roles of the target SA
            resource=service_account,
        )
        response = request.execute()
        roles = []

        if 'bindings' in response:
            for binding in response['bindings']:
                if 'members' in binding:
                    for member in binding['members']:
                        # Extract the email or serviceaccount identifier part after the ':' character
                        _, member_identifier = member.split(':', 1)
                        # Check if the extracted identifier matches the token user email to understand if it has the role
                        if member_identifier == self.user_email:
                            roles.append(binding['role'])
        return roles

    @handle_api_ratelimit
    def get_project_roles(self, project_id):
        """Get Project-level roles of the IAM User/SA from the IAM Policy"""
        request = self.resource_manager_service.projects().getIamPolicy(
            resource=project_id,
            body={}
        )
        response = request.execute()
        roles = []

        if 'bindings' in response:
            for binding in response['bindings']:
                if 'members' in binding:
                    for member in binding['members']:
                        # Handle different member types properly
                        if ':' in member:
                            member_type, member_id = member.split(':', 1)
                            # Check against both user and service account formats
                            if member_id == self.user_email:
                                roles.append(binding['role'])
                        # Handle special cases like allUsers/allAuthenticatedUsers
                        else:
                            if member == self.user_email:
                                roles.append(binding['role'])
        return roles

    @handle_api_ratelimit
    def get_projects(self):
        try:
            if self.project_id:  # Check if a specific project was requested
                try:
                    # Verify project exists and is accessible
                    request = self.resource_manager_service.projects().get(projectId=self.project_id)
                    response = request.execute()
                    return [self.project_id]  # Return single project ID as list
                except Exception as e:
                    print_color(f"Error accessing project {self.project_id}", color="red")
                    # Fall back to all projects if inaccessible
            
            # Default behavior returns all projects
            request = self.resource_manager_service.projects().list()
            response = request.execute()
            return [project['projectId'] for project in response['projects']]

        except Exception as e:
            print_color(f"Failed to get projects: {e}", color="red")
            raise e

    def check_permission(self, role):
        """Check if the target role has iam.serviceAccountKeys.create permission"""
        try:
            if "projects/" in role:
                request = self.iam_service.projects().roles().get(name=role)
            else:
                request = self.iam_service.roles().get(name=role)

            response = request.execute()
            return 'iam.serviceAccountKeys.create' in response.get('includedPermissions', [])
        except Exception as e:
            if self.verbose:
                print_color(f"Error checking role {role}: {str(e)}", color="yellow")
            return False

    def enumerate_service_accounts(self):
        any_service_account_with_key_permission = False
        for project_id in self.get_projects():
            request = self.iam_service.projects().serviceAccounts().list(name='projects/' + project_id)
            response = request.execute()
            if 'accounts' in response:
                for account in response['accounts']:
                    project_roles = self.get_project_roles(project_id)
                    service_account_roles = self.get_service_account_roles(account['name'])
                    all_roles = list(set(project_roles + service_account_roles))
                    if any(self.check_permission(role) for role in all_roles):
                        self.print_service_account_details(account, all_roles)
                        self.key_creator.create_service_account_key(account['name'])
                        any_service_account_with_key_permission = True
                    elif self.verbose:
                        self.print_service_account_details(account)
                        print_color('✗ No relevant roles found', color="red")
                        print('---')
        if not any_service_account_with_key_permission:
            print("No GCP Service Accounts roles found with the relevant key permissions")

    def print_service_account_details(self, account, roles=None):
        print_color("→ Service Account Details", color="magenta")
        print_color('  Name: ' + account['name'], color="cyan")
        print_color('  Email: ' + account['email'], color="cyan")
        print_color('  UniqueId: ' + account['uniqueId'], color="cyan")
        if roles:
            print_color(f'  Roles: {", ".join(roles)}', color="green")

    @handle_api_ratelimit
    def list_projects(self):
        """List accessible GCP projects with details and access information"""
        try:
            request = self.resource_manager_service.projects().list()
            response = request.execute()
            projects = response.get('projects', [])
            
            for project in projects:
                project_id = project['projectId']
                project['roles'] = self.get_project_roles(project_id)
            return projects
        except Exception as e:
            print_color(f"Failed to list projects: {e}", color="red")
            raise e


