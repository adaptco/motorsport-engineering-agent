import os
import time
import jwt
import httpx

GITHUB_API = "https://api.github.com"
APP_ID = os.environ.get("GITHUB_APP_ID")
PRIVATE_KEY = os.environ.get("GITHUB_APP_PRIVATE_KEY", "").replace("\\n", "\n")

def build_app_jwt() -> str:
    """
    Build a JSON Web Token (JWT) for GitHub App authentication.
    
    The JWT is signed with the app's private key and includes:
    - iat: Issued at time (60 seconds ago to account for clock skew)
    - exp: Expiration time (10 minutes from now)
    - iss: Issuer (the GitHub App ID)
    
    This JWT is used to authenticate as the GitHub App for API calls.
    """
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + 540,
        "iss": APP_ID,
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")

def create_installation_token(installation_id: int) -> str:
    """
    Create an installation access token for a specific GitHub App installation.
    
    Uses the app JWT to request an installation token from GitHub's API.
    The installation token has permissions based on the app's installation configuration
    and is valid for 1 hour.
    
    Args:
        installation_id: The ID of the GitHub App installation
        
    Returns:
        The installation access token string
    """
    app_jwt = build_app_jwt()
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            f"{GITHUB_API}/app/installations/{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
            },
        )
        resp.raise_for_status()
        return resp.json()["token"]
