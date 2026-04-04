import os
import time
import logging
import asyncio
import jwt
import httpx
from typing import Optional

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("github_app")

GITHUB_API = "https://api.github.com"
APP_ID = os.environ.get("GITHUB_APP_ID")
# Ensure newline characters are correctly handled for the RSA private key
PRIVATE_KEY = os.environ.get("GITHUB_APP_PRIVATE_KEY", "").replace("\\n", "\n")

def build_app_jwt() -> str:
    """Builds a JWT for GitHub App authentication."""
    if not APP_ID or not PRIVATE_KEY:
        logger.error("GITHUB_APP_ID or GITHUB_APP_PRIVATE_KEY is not set")
        raise RuntimeError("Missing GitHub App configuration")

    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + 540,  # Max 10 minutes
        "iss": APP_ID,
    }
    try:
        return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
    except Exception as e:
        logger.error(f"Failed to encode JWT: {e}")
        raise

def create_installation_token(installation_id: int) -> str:
    """Creates an installation access token for the given installation ID."""
    logger.info(f"Requesting installation token for ID: {installation_id}")
    app_jwt = build_app_jwt()

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{GITHUB_API}/app/installations/{installation_id}/access_tokens",
                headers={
                    "Authorization": f"Bearer {app_jwt}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
            )
            if resp.status_code != 201:
                logger.error(f"Failed to create token: {resp.status_code} - {resp.text}")
                resp.raise_for_status()

            token_data = resp.json()
            logger.info(f"Successfully generated token for installation {installation_id}")
            return token_data["token"]
    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred while creating installation token: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating installation token: {e}")
        raise

class GitHubAppClient:
    """A hardened client for interacting with the GitHub API as an App."""
    def __init__(self, installation_id: int):
        self.installation_id = installation_id
        self._token: Optional[str] = None
        self._token_expires_at: float = 0

    async def get_token(self) -> str:
        """Retrieves a valid installation token, refreshing if necessary."""
        # Refresh token 5 minutes before expiration
        if not self._token or time.time() > self._token_expires_at - 300:
            self._token = create_installation_token(self.installation_id)
            # In a real scenario, we would parse the 'expires_at' from the response.
            # Defaulting to 1 hour for now.
            self._token_expires_at = time.time() + 3600
        return self._token
