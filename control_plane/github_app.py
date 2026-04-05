import os
import time

import jwt
import requests

from shared.circuit_breaker import CircuitBreaker

GITHUB_API = "https://api.github.com"
APP_ID = os.environ.get("GITHUB_APP_ID")
PRIVATE_KEY = os.environ.get("GITHUB_APP_PRIVATE_KEY", "").replace("\\n", "\n")
GITHUB_API_MAX_RETRIES = int(os.environ.get("GITHUB_API_MAX_RETRIES", "2"))
GITHUB_API_BREAKER = CircuitBreaker.from_env("GITHUB_API")


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

    def _request_token() -> str:
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

    attempts = max(1, GITHUB_API_MAX_RETRIES)
    last_exc: Exception | None = None
    for _ in range(attempts):
        try:
            return GITHUB_API_BREAKER.call(_request_token)
        except Exception as exc:
            last_exc = exc
    raise RuntimeError(f"github_installation_token_failed_after_{attempts}_attempts: {last_exc}")
