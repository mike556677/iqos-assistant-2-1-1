# IQOS Assistant 2.1.1

Package includes a portable plugin manifest, reusable workflow skill, OpenAPI 3.1 specification, and a FastAPI starter backend.

## Included
- File search over text-readable files in a configured local folder
- Extractive starter summaries
- Safe preview-first rename/move operations
- Persistent reminder records
- OpenAPI schema and Dockerfile

## Not yet connected
This is a scaffold, not a fully deployed cloud service. Google Drive/OneDrive OAuth, ChatGPT uploaded-file ingestion, push notifications/scheduler, and semantic AI summarization need provider credentials and deployment. No credentials are embedded.

## Next steps
1. Deploy `backend/` to a secure HTTPS host.
2. Configure authentication and persistent storage.
3. Add authorized cloud provider connectors and a scheduler.
4. Replace the placeholder server URL in `openapi.yaml`.
5. Connect the hosted API/MCP server in ChatGPT and test with sample data.
