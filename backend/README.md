# IQOS Assistant API backend

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs: `http://127.0.0.1:8000/docs`.

## Data and limitations

- Put text-readable files in `IQOS_DATA_DIR/files` (default `./data/files`).
- Reminder records persist in `IQOS_DATA_DIR/reminders.json`; actual notifications require a scheduler/provider.
- Cloud connectors (Google Drive/OneDrive) are not included because each needs provider OAuth configuration, credentials, and authorization. Uploaded files must be ingested by a host-specific upload/connector flow.
- The included summarizer is extractive starter logic, not an AI model.
- Before deployment, use HTTPS, authentication, rate limiting, audit logs, and a persistent volume. Do not expose this starter backend publicly without security hardening.
- Change the placeholder server URL in `../openapi.yaml` to the deployed HTTPS API URL.
