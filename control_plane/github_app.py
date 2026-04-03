import os
import time
import jwt
import requests

GITHUB_API = "https://api.github.com"
APP_ID = os.environ.get("GITHUB_APP_ID")
PRIVATE_KEY = os.environ.get("GITHUB_APP_PRIVATE_KEY", "").replace("\\n", "\n")

def build_app_jwt() -> str:
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + 540,
        "iss": APP_ID,
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")

def create_installation_token(installation_id: int) -> str:
    app_jwt = build_app_jwt()
    resp = requests.post(
        f"{GITHUB_API}/app/installations/{installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["token"]
