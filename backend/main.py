"""Starter backend for IQOS Assistant 2.1.1.

Local-only reference implementation. Cloud file providers and actual notification
 delivery require OAuth/provider integrations and a deployed scheduler.
"""
from __future__ import annotations
import os, json, uuid, shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Literal
from fastapi import FastAPI, HTTPException, Header, Depends
import secrets
from pydantic import BaseModel, Field

ROOT = Path(os.getenv("IQOS_DATA_DIR", "./data")).resolve()
FILES_DIR = (ROOT / "files").resolve()
REMINDERS_FILE = ROOT / "reminders.json"
FILES_DIR.mkdir(parents=True, exist_ok=True)
ROOT.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="IQOS Assistant API", version="2.1.1")
def verify_api_key(x_iqos_api_key: str = Header(default="")):
    expected_key = os.getenv("IQOS_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="API key is not configured"
        )

    if not secrets.compare_digest(x_iqos_api_key, expected_key):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )

class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    source: Literal["all", "local", "uploaded", "cloud"] = "all"
    limit: int = Field(default=20, ge=1, le=100)

class FileRecord(BaseModel):
    id: str
    name: str
    path: str
    source: str = "local"
    snippet: str = ""
    modified_at: str

class ReminderRequest(BaseModel):
    title: str = Field(min_length=1)
    due_at: str
    timezone: str = "Europe/Nicosia"
    recurrence: Literal["none", "daily", "weekly", "monthly"] = "none"

def read_reminders():
    if not REMINDERS_FILE.exists(): return []
    try: return json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
    except (ValueError, OSError): return []

def write_reminders(items):
    REMINDERS_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

def file_record(p: Path, snippet=""):
    rel = p.relative_to(FILES_DIR).as_posix()
    return {"id": rel, "name": p.name, "path": rel, "source": "local", "snippet": snippet[:400], "modified_at": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat()}

@app.get("/health")
def health(): return {"status": "ok", "version": "2.1.1"}


@app.get("/files", dependencies=[Depends(verify_api_key)])
def list_files():
    return {"files": [file_record(p) for p in FILES_DIR.rglob("*") if p.is_file()]}

@app.post("/files/search", dependencies=[Depends(verify_api_key)])
def search_files(req: SearchRequest):
    if req.source == "cloud": return {"results": [], "notice": "No cloud provider is configured. Add an OAuth-authorized provider connector first."}
    terms = req.query.casefold().split()
    results = []
    for p in FILES_DIR.rglob("*"):
        if not p.is_file(): continue
        try:
            if p.stat().st_size > 5_000_000: continue
            raw = p.read_text(encoding="utf-8", errors="ignore")
        except OSError: continue
        haystack = (p.name + " " + raw).casefold()
        if all(t in haystack for t in terms):
            pos = haystack.find(terms[0]) if terms else 0
            snippet = raw[max(0, pos-100):pos+300] if raw else ""
            results.append(file_record(p, snippet))
            if len(results) >= req.limit: break
    return {"results": results, "notice": "Search is limited to text-readable files in the configured local data directory; uploaded/cloud sources need provider integration."}

@app.post("/files/summarize", dependencies=[Depends(verify_api_key)])
def summarize(payload: dict):
    text = str(payload.get("text", "")).strip()
    if not text: raise HTTPException(400, "text is required")
    style = payload.get("style", "brief")
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    count = 3 if style == "brief" else (10 if style == "detailed" else 6)
    summary = ". ".join(sentences[:count])
    if summary and not summary.endswith("."): summary += "."
    if style == "bullets": summary = "\n".join("- " + s.strip() for s in sentences[:count])
    return {"summary": summary, "word_count": len(text.split()), "note": "Extractive starter summary; connect an LLM summarization service for semantic summaries."}

@app.post("/files/organize", dependencies=[Depends(verify_api_key)])
def organize(payload: dict):
    file_id = str(payload.get("file_id", ""))
    action = payload.get("action")
    apply = bool(payload.get("apply", False))
    candidate = (FILES_DIR / file_id).resolve()
    if not candidate.is_relative_to(FILES_DIR) or not candidate.is_file(): raise HTTPException(404, "File not found")
    if action == "rename":
        new_name = str(payload.get("new_name", "")).strip()
        if not new_name or Path(new_name).name != new_name: raise HTTPException(400, "new_name must be a filename only")
        dest = candidate.with_name(new_name)
    elif action == "move":
        folder = str(payload.get("destination_folder", "")).strip()
        dest = (FILES_DIR / folder / candidate.name).resolve()
        if not dest.is_relative_to(FILES_DIR): raise HTTPException(400, "Invalid destination")
    else: raise HTTPException(400, "action must be rename or move")
    if dest.exists() and dest != candidate: raise HTTPException(409, "Destination already exists")
    if not apply: return {"applied": False, "message": "Preview only. Re-submit with apply=true after explicit user confirmation.", "file": file_record(candidate), "proposed_path": dest.relative_to(FILES_DIR).as_posix()}
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(candidate), str(dest))
    return {"applied": True, "message": "File operation completed", "file": file_record(dest)}

@app.get("/reminders", dependencies=[Depends(verify_api_key)])
def list_reminders(): return {"reminders": read_reminders()}

@app.post("/reminders", status_code=201, dependencies=[Depends(verify_api_key)])
def create_reminder(req: ReminderRequest):
    try:
        parsed = datetime.fromisoformat(req.due_at.replace("Z", "+00:00"))
    except ValueError: raise HTTPException(400, "due_at must be ISO 8601 date-time")
    if parsed.tzinfo is None: raise HTTPException(400, "due_at must include a timezone offset")
    items = read_reminders()
    item = {"id": str(uuid.uuid4()), "title": req.title, "due_at": parsed.isoformat(), "timezone": req.timezone, "recurrence": req.recurrence, "created_at": datetime.now(timezone.utc).isoformat()}
    items.append(item); write_reminders(items)
    return {**item, "notice": "Saved to the reminder store. Notifications will not fire until a scheduler/notification provider is configured."}

@app.delete("/reminders/{reminder_id}", dependencies=[Depends(verify_api_key)])
def delete_reminder(reminder_id: str):
    items = read_reminders(); updated = [x for x in items if x.get("id") != reminder_id]
    if len(updated) == len(items): raise HTTPException(404, "Reminder not found")
    write_reminders(updated)
    return {"deleted": True}
