"""worker/github_app_client module."""

import os
from control_plane.github_app import create_installation_token

def get_installation_token(installation_id: int | None = None) -> str:
    resolved = installation_id or int(os.environ["GITHUB_APP_INSTALLATION_ID"])
    return create_installation_token(resolved)
