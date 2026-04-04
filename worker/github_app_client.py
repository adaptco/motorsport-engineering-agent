import os
from control_plane.github_app import create_installation_token

def get_installation_token(installation_id: int | None = None) -> str:
    """
    Get a GitHub installation access token for the specified installation.
    
    If no installation_id is provided, uses GITHUB_APP_INSTALLATION_ID from environment.
    This token is used for authenticated API calls and git operations on behalf of the GitHub App.
    """
    resolved = installation_id or int(os.environ["GITHUB_APP_INSTALLATION_ID"])
    return create_installation_token(resolved)
