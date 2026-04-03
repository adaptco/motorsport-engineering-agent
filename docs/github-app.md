# GitHub App scaffold

The control plane expects a GitHub App with these environment variables:

- `GITHUB_APP_ID`
- `GITHUB_APP_INSTALLATION_ID`
- `GITHUB_APP_PRIVATE_KEY`
- `GITHUB_WEBHOOK_SECRET`

Use `control_plane/github_app_manifest.json` as the initial manifest scaffold.

## Required permissions

- Actions: write
- Checks: write
- Contents: write
- Metadata: read
- Pull requests: write

## Webhook endpoint

- `POST /github/webhook`
