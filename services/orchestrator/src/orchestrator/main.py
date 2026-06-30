from __future__ import annotations

import base64
import json
import os
import re
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated, Any

import httpx
from agentkit.auth import UserContext, get_current_user
from agentkit.guardrails import GuardrailViolation, check_message
from agentkit.market import get_market
from agentkit.portfolio import DEALS, GEO, SECTOR, TOP_DEALS, get_metrics
from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from orchestrator.graph import run_deep_turn_payloads, run_turn

app = FastAPI(title="Orchestrator", version="0.1.0")

_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
_OCR_MODEL = os.getenv("MODEL_OCR", "llava:7b")
_VOICE_URL = os.getenv("VOICE_URL", "http://localhost:8006").rstrip("/")
_MAX_ATTACHMENT_BYTES = 8 * 1024 * 1024
_AGENT_HEALTH_URLS: dict[str, str] = {
    "financial": os.getenv("AGENT_FINANCIAL_URL", "http://localhost:8001").rstrip("/"),
    "market": os.getenv("AGENT_MARKET_URL", "http://localhost:8002").rstrip("/"),
    "docs": os.getenv("AGENT_DOCS_URL", "http://localhost:8003").rstrip("/"),
    "action": os.getenv("AGENT_ACTION_URL", "http://localhost:8004").rstrip("/"),
    "qa": os.getenv("AGENT_QA_URL", "http://localhost:8005").rstrip("/"),
    "voice": _VOICE_URL,
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory GDPR deletion log (persist to DB in production)
_DELETION_LOG: list[dict[str, Any]] = []
_DOCUMENT_LIBRARY: dict[str, list[dict[str, Any]]] = {}


@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


# ── Health ─────────────────────────────────────────────────────────────────────


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "orchestrator"}


@app.get("/api/mesh/health")
async def mesh_health(  # noqa: B008
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    """Return live health for the orchestrator, specialist agents, and voice service."""
    services: list[dict[str, Any]] = [
        {
            "id": "orchestrator",
            "name": "Orchestrator",
            "status": "ok",
            "latency_ms": 0.0,
            "url": "local",
            "detail": "API online",
        }
    ]
    async with httpx.AsyncClient(timeout=4) as client:
        for service_id, base_url in _AGENT_HEALTH_URLS.items():
            started = datetime.now(UTC)
            try:
                resp = await client.get(f"{base_url}/health")
                elapsed = (datetime.now(UTC) - started).total_seconds() * 1000
                data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                status = "ok" if resp.status_code == 200 and data.get("status", "ok") == "ok" else "degraded"
                services.append(
                    {
                        "id": service_id,
                        "name": data.get("service", service_id),
                        "status": status,
                        "latency_ms": round(elapsed, 1),
                        "url": base_url,
                        "detail": data,
                    }
                )
            except Exception as exc:
                services.append(
                    {
                        "id": service_id,
                        "name": service_id,
                        "status": "down",
                        "latency_ms": None,
                        "url": base_url,
                        "detail": str(exc),
                    }
                )
    ok = sum(1 for service in services if service["status"] == "ok")
    return {
        "status": "ok" if ok == len(services) else "degraded",
        "checked_at": datetime.now(UTC).isoformat(),
        "services": services,
    }


# ── Auth ───────────────────────────────────────────────────────────────────────


@app.get("/auth/verify")
async def auth_verify(  # noqa: B008
    response: Response,
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> dict[str, str]:
    """Traefik forward-auth — validates JWT and injects user headers."""
    response.headers["X-User-Id"] = user.user_id
    response.headers["X-User-Email"] = user.email
    response.headers["X-User-Roles"] = ",".join(user.roles)
    return {"ok": "true"}


@app.get("/api/me")
async def me(  # noqa: B008
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> dict[str, object]:
    return {
        "user_id": user.user_id,
        "email": user.email,
        "roles": user.roles,
    }


# ── Portfolio & market data (read-only, auth-protected) ─────────────────────────


@app.get("/api/portfolio/summary")
async def portfolio_summary(  # noqa: B008
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    return get_metrics()


@app.get("/api/portfolio/allocation")
async def portfolio_allocation(  # noqa: B008
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    return {"geography": GEO, "sector": SECTOR}


@app.get("/api/portfolio/deals")
async def portfolio_deals(  # noqa: B008
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> list[dict[str, Any]]:
    return DEALS


@app.get("/api/portfolio/top-deals")
async def portfolio_top_deals(  # noqa: B008
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> list[dict[str, Any]]:
    return TOP_DEALS


@app.get("/api/market")
async def market(  # noqa: B008
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    return get_market()


# ── Chat (SSE streaming) ───────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    display_message: str = ""
    conversation_id: str = ""
    mode: str = "instant"


@app.post("/api/chat")
async def chat(  # noqa: B008
    request: Request,
    body: ChatRequest,
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> StreamingResponse:
    """Stream a chat turn through the LangGraph supervisor."""
    try:
        safe_message = check_message(body.message)
    except GuardrailViolation as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    conv_id = body.conversation_id or str(uuid.uuid4())
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    async def _sse() -> AsyncIterator[str]:
        if body.mode == "deep":
            display_message = check_message(body.display_message or body.message)
            async for payload in run_deep_turn_payloads(
                display_message,
                conv_id,
                user.user_id,
                execution_message=safe_message,
                correlation_id=correlation_id,
            ):
                event_type = "reasoning" if payload["type"] == "reasoning" else "token"
                data = json.dumps(
                    {
                        event_type: payload["content"],
                        "conversation_id": conv_id,
                    }
                )
                yield f"data: {data}\n\n"
        else:
            display_message = check_message(body.display_message or body.message)
            async for token in run_turn(
                display_message,
                conv_id,
                user.user_id,
                execution_message=safe_message,
                correlation_id=correlation_id,
            ):
                payload = json.dumps({"token": token, "conversation_id": conv_id})
                yield f"data: {payload}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_sse(), media_type="text/event-stream")


async def _extract_text_file(file: UploadFile, data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


async def _extract_audio(file: UploadFile, data: bytes) -> str:
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            files = {
                "audio": (file.filename or "audio.webm", data, file.content_type or "audio/webm")
            }
            resp = await client.post(f"{_VOICE_URL}/voice/transcribe", files=files)
            resp.raise_for_status()
            return str(resp.json().get("transcript", "")).strip()
    except Exception as exc:
        return f"[Audio transcription unavailable: {exc}]"


async def _extract_image(file: UploadFile, data: bytes) -> str:
    try:
        prompt = (
            "Extract all readable text from this image. If it is a financial document or screenshot, "
            "preserve numbers, headings, dates, currencies, and table-like structure. Return only the extracted text."
        )
        payload = {
            "model": _OCR_MODEL,
            "prompt": prompt,
            "images": [base64.b64encode(data).decode()],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(f"{_OLLAMA_URL}/api/generate", json=payload)
            resp.raise_for_status()
            return str(resp.json().get("response", "")).strip()
    except Exception as exc:
        return f"[OCR unavailable for {file.filename}: {exc}]"


@app.get("/api/attachments/status")
async def attachment_status(  # noqa: B008
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    installed = False
    ollama_online = False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{_OLLAMA_URL}/api/tags")
            resp.raise_for_status()
            ollama_online = True
            models = resp.json().get("models", [])
            installed = any(
                model.get("name") == _OCR_MODEL or model.get("model") == _OCR_MODEL
                for model in models
            )
    except Exception:
        pass

    return {
        "ocr": {
            "engine": "ollama",
            "model": _OCR_MODEL,
            "installed": installed,
            "ready": ollama_online and installed,
        },
        "ollama_url": _OLLAMA_URL,
        "voice_url": _VOICE_URL,
        "limits": {"max_files": 12, "max_file_mb": _MAX_ATTACHMENT_BYTES // (1024 * 1024)},
    }


@app.post("/api/attachments/extract")
async def extract_attachments(  # noqa: B008
    request: Request,
    files: Annotated[list[UploadFile], File(...)],
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    """Extract text context from text, image, and audio attachments."""
    extracted: list[dict[str, Any]] = []
    saved_docs = _DOCUMENT_LIBRARY.setdefault(user.user_id, [])
    for file in files[:12]:
        data = await file.read()
        name = file.filename or "attachment"
        content_type = file.content_type or ""
        if len(data) > _MAX_ATTACHMENT_BYTES:
            extracted.append(
                {
                    "name": name,
                    "kind": "unsupported",
                    "content": "",
                    "error": "File is larger than the 8 MB demo limit.",
                }
            )
            continue

        if content_type.startswith("text/") or name.lower().endswith(
            (".txt", ".md", ".csv", ".json")
        ):
            content = await _extract_text_file(file, data)
            kind = "text"
        elif content_type.startswith("image/") or name.lower().endswith(
            (".png", ".jpg", ".jpeg", ".webp")
        ):
            content = await _extract_image(file, data)
            kind = "image"
        elif content_type.startswith("audio/") or name.lower().endswith(
            (".wav", ".mp3", ".m4a", ".webm", ".ogg")
        ):
            content = await _extract_audio(file, data)
            kind = "audio"
        else:
            content = ""
            kind = "unsupported"

        attachment = {
            "id": str(uuid.uuid4()),
            "name": name,
            "kind": kind,
            "content": content[:20_000],
            "size": len(data),
            "created_at": datetime.now(UTC).isoformat(),
            "correlation_id": getattr(request.state, "correlation_id", ""),
            **({"error": "Unsupported file type."} if kind == "unsupported" else {}),
        }
        extracted.append(attachment)
        if kind != "unsupported":
            saved_docs.append(attachment)
    return {"attachments": extracted}


@app.get("/api/documents")
async def list_documents(  # noqa: B008
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    documents = _DOCUMENT_LIBRARY.get(user.user_id, [])
    return {
        "documents": [
            {
                "id": doc["id"],
                "name": doc["name"],
                "kind": doc["kind"],
                "size": doc.get("size", 0),
                "created_at": doc["created_at"],
                "preview": doc.get("content", "")[:240],
                "correlation_id": doc.get("correlation_id", ""),
            }
            for doc in documents
        ]
    }


@app.get("/api/documents/{document_id}/export")
async def export_document(  # noqa: B008
    document_id: str,
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> Response:
    for doc in _DOCUMENT_LIBRARY.get(user.user_id, []):
        if doc["id"] == document_id:
            filename = re.sub(r"[^a-zA-Z0-9_.-]+", "_", doc["name"]) or "document.txt"
            return Response(
                doc.get("content", ""),
                media_type="text/plain; charset=utf-8",
                headers={"Content-Disposition": f'attachment; filename="{filename}.txt"'},
            )
    raise HTTPException(status_code=404, detail="Document not found")


@app.delete("/api/documents/{document_id}")
async def delete_document(  # noqa: B008
    document_id: str,
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> dict[str, str]:
    documents = _DOCUMENT_LIBRARY.get(user.user_id, [])
    remaining = [doc for doc in documents if doc["id"] != document_id]
    if len(remaining) == len(documents):
        raise HTTPException(status_code=404, detail="Document not found")
    _DOCUMENT_LIBRARY[user.user_id] = remaining
    return {"status": "deleted", "document_id": document_id}


@app.get("/api/documents/history")
async def documents_history(  # noqa: B008
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> dict[str, Any]:
    documents = _DOCUMENT_LIBRARY.get(user.user_id, [])
    return {
        "events": [
            {
                "type": "uploaded",
                "document_id": doc["id"],
                "name": doc["name"],
                "kind": doc["kind"],
                "timestamp": doc["created_at"],
                "correlation_id": doc.get("correlation_id", ""),
            }
            for doc in documents
        ]
    }


# ── GDPR ───────────────────────────────────────────────────────────────────────


@app.delete("/api/gdpr/delete-my-data")
async def gdpr_delete(  # noqa: B008
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> dict[str, str]:
    """
    GDPR Article 17 — Right to Erasure.
    Logs the deletion request; production should cascade to all data stores.
    """
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "user_id": user.user_id,
        "email": user.email,
        "action": "delete_all_personal_data",
        "status": "acknowledged",
        "note": (
            "Production: cascade delete to Postgres (conversations, audit_log rows), "
            "Qdrant vectors, Langfuse traces for this user."
        ),
    }
    _DELETION_LOG.append(entry)
    return {
        "status": "acknowledged",
        "user_id": user.user_id,
        "message": (
            "Your personal data deletion request has been logged. "
            "Data will be purged within 30 days per GDPR Article 17."
        ),
    }


@app.get("/api/gdpr/deletion-log")
async def gdpr_log(  # noqa: B008
    user: UserContext = Depends(get_current_user),  # noqa: B008
) -> list[dict[str, Any]]:
    """Return deletion log (admin-only in production — requires 'admin' role)."""
    if "admin" not in user.roles and "advisor" not in user.roles:
        raise HTTPException(status_code=403, detail="Forbidden")
    return _DELETION_LOG
