# Deploy IQOS Assistant 2.1.1 to Render

## Before you begin

This project is a starter backend, not a production-ready service. Do not put sensitive or confidential files into it until authentication and cloud-provider authorization have been implemented and tested. The current backend does not include Google Drive/OneDrive OAuth, ChatGPT upload ingestion, or outbound reminder notifications.

## Deploy

1. Create a private GitHub repository and upload the contents of this folder (the `iqos-assistant-2.1.1` folder should be the repository root).
2. Sign in to Render and connect the GitHub account.
3. In Render choose **New → Blueprint**, select the repository, and deploy the `render.yaml` blueprint.
4. After the service deploys, open its `https://<service-name>.onrender.com/health` endpoint. It should return `{"status":"ok","version":"2.1.1"}`.
5. Open `/openapi.json` on the service to see FastAPI's generated OpenAPI document.
6. Update `servers[0].url` in `openapi.yaml` to the actual HTTPS service URL before using the API spec in any client.

## Important security limitation

The starter API currently has no authentication. Keep it private/unexposed until bearer/API-key authentication has been implemented. A public endpoint can let strangers read, move, or rename files that have been uploaded into its local data directory and manipulate reminder records.

## Persistent storage note

The Blueprint attaches a 1 GB persistent disk at `/app/data` and sets `IQOS_DATA_DIR=/app/data`. The free service may spin down when idle; see Render's current plan limits before relying on scheduled jobs or time-sensitive reminders. A disk preserves the local records, but it does not create notifications.

## Hosting documentation

Render's official FastAPI deployment guide: https://render.com/docs/deploy-fastapi
Render Blueprint documentation: https://render.com/docs/blueprint-spec
