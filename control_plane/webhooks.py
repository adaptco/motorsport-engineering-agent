"""control_plane/webhooks module."""

import hashlib
import hmac
import os

from fastapi import APIRouter, Header, HTTPException, Request

from control_plane.repository import correlate_workflow_run, store_webhook

router = APIRouter(prefix="/github", tags=["github"])


def get_webhook_secret() -> str | None:
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "").strip()
    return secret or None


def verify_signature(body: bytes, signature: str | None) -> None:
    secret = get_webhook_secret()
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="webhook configuration error: GITHUB_WEBHOOK_SECRET is not set",
        )
    if not signature:
        raise HTTPException(status_code=401, detail="missing signature")
    # GitHub webhook signature format is "sha256=<hexdigest>" over raw request bytes.
    digest = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    # Constant-time comparison prevents timing attacks on signature verification.
    if not hmac.compare_digest(digest, signature):
        raise HTTPException(status_code=401, detail="invalid signature")


@router.post("/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None),
):
    body = await request.body()
    verify_signature(body, x_hub_signature_256)
    # Only parse JSON after signature verification so untrusted bodies are rejected early.
    payload = await request.json()
    repo_slug = payload.get("repository", {}).get("full_name")
    store_webhook(x_github_delivery or "unknown", x_github_event or "unknown", repo_slug, payload)

    if x_github_event == "workflow_run":
        run_id = str(payload.get("workflow_run", {}).get("id"))
        correlate_workflow_run(repo_slug or "", run_id, payload)

    return {"ok": True}
