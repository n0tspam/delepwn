from delepwn.utils.output import print_color
from delepwn.utils.api import handle_api_ratelimit

class DomainUserEnumerator:
    """ Find target Workspace users using GCP projects role enumeration. returns one email address per distinct domain org """
    def __init__(self, gcp_project_enumerator):
        self.gcp_project_enumerator = gcp_project_enumerator
        self.single_test_email = {}

    @handle_api_ratelimit
    def list_unique_domain_users(self):
        """List unique domain users across projects (excluding service accounts)"""
        unique_domains = {}
        for project_id in self.gcp_project_enumerator.get_projects():
            resource_manager_service = self.gcp_project_enumerator.resource_manager_service
            request = resource_manager_service.projects().getIamPolicy(resource=project_id, body={})
            response = request.execute()

            if 'bindings' in response:
                for binding in response['bindings']:
                    if 'members' in binding:
                        for member in binding['members']:
                            if member.startswith('user:'):
                                email = member.split(':')[1]
                                # exclude GCP service accounts
                                if '@' in email and not email.endswith('.gserviceaccount.com'):
                                    domain = email.split('@')[1]
                                    if domain not in unique_domains:
                                        unique_domains[domain] = email
                                        break
        self.single_test_email = unique_domains
        return unique_domains


    def print_unique_domain_users(self):
        unique_domain_users = self.list_unique_domain_users()
        if unique_domain_users:
            print_color("\n✓ Domain IAM Users Found", color="cyan")
            print_color("-" * 50, color="blue")
            for domain, user in unique_domain_users.items():
                print_color(f"Domain: {domain}", color="white")
                print_color(f"User: {user}", color="white")
                print_color("-" * 50, color="blue")
        else:
            print_color("\nNo domain IAM users found in specified projects", color="yellow")

    def get_first_valid_domain_user(self):
        """Get the first valid domain user email found during enumeration"""
        try:
            self.list_unique_domain_users()
            if self.single_test_email:
                first_email = next(iter(self.single_test_email.values()))
                return first_email
            return None
        except Exception as e:
            print_color(f"Error finding valid domain user: {str(e)}", color="red")
            return None

