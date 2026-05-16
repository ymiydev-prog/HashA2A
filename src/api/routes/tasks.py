"""A2A-compatible Task API — lifecycle, context, artifacts, and status."""

import json
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import Response

from core.task_manager import TaskManager
from core.context_manager import ContextManager
from models.schemas import (
    TaskObject, TaskStatus, MessagePart, PartType, Artifact,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

_task_mgr: TaskManager | None = None
_ctx_mgr: ContextManager | None = None
_ARTIFACT_DIR = "/tmp/hasha2a_artifacts"


def get_mgr() -> TaskManager:
    global _task_mgr, _ctx_mgr
    if _task_mgr is None:
        _ctx_mgr = ContextManager()
        _task_mgr = TaskManager(context_manager=_ctx_mgr)
    return _task_mgr


def get_ctx() -> ContextManager:
    get_mgr()
    return _ctx_mgr


def _ensure_artifact_dir():
    os.makedirs(_ARTIFACT_DIR, exist_ok=True)


# ─── Tasks ───────────────────────────────────────────────────────


@router.post("", status_code=201)
async def create_task(
    agent_id: str = "hasha2a",
    context_id: str | None = None,
):
    mgr = get_mgr()
    ctx = get_ctx()
    if context_id and not ctx.get_context(context_id):
        new_ctx = ctx.create_context(agent_id=agent_id)
        context_id = new_ctx.context_id
    task = mgr.create_task(agent_id=agent_id, context_id=context_id)
    return task.model_dump(mode="json")


@router.get("/{task_id}")
async def get_task(task_id: str):
    mgr = get_mgr()
    task = mgr.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.model_dump(mode="json")


@router.get("")
async def list_tasks(
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
):
    mgr = get_mgr()
    s = TaskStatus(status) if status else None
    tasks = mgr.list_tasks(status=s, limit=limit)
    return {
        "tasks": [t.model_dump(mode="json") for t in tasks],
        "count": len(tasks),
        "total_by_status": mgr.count_by_status(),
    }


@router.post("/{task_id}/parts")
async def add_part(task_id: str, part: MessagePart):
    mgr = get_mgr()
    ok = mgr.add_part(task_id, part)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "ok", "task_id": task_id}


@router.post("/{task_id}/transition")
async def transition_task(task_id: str, body: dict):
    new_status = body.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="status required")
    mgr = get_mgr()
    try:
        s = TaskStatus(new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")
    ok = mgr.update_status(task_id, s)
    if not ok:
        raise HTTPException(status_code=404, detail="Task not found")
    task = mgr.get_task(task_id)
    return task.model_dump(mode="json")


@router.post("/{task_id}/complete")
async def complete_task(task_id: str, body: dict = {}):
    mgr = get_mgr()
    summary = body.get("summary")
    artifact = mgr.complete(task_id, summary=summary)
    if not artifact:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "completed", "artifact": artifact.model_dump(mode="json")}


# ─── Artifacts ────────────────────────────────────────────────────


@router.post("/{task_id}/artifacts", status_code=201)
async def add_artifact(task_id: str, parts: list[MessagePart], name: str | None = None):
    mgr = get_mgr()
    artifact = mgr.add_artifact(task_id, parts, name=name)
    if not artifact:
        raise HTTPException(status_code=404, detail="Task not found")
    return artifact.model_dump(mode="json")


@router.post("/{task_id}/artifacts/upload", status_code=201)
async def upload_artifact(task_id: str, file: UploadFile = File(...)):
    mgr = get_mgr()
    _ensure_artifact_dir()
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename or "file")[1] or ".bin"
    save_path = os.path.join(_ARTIFACT_DIR, f"{file_id}{ext}")
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    parts = [MessagePart(
        type=PartType.FILE,
        file_uri=save_path,
        filename=file.filename or "file",
        content_type=file.content_type or "application/octet-stream",
    )]
    artifact = mgr.add_artifact(task_id, parts, name=file.filename)
    if not artifact:
        raise HTTPException(status_code=404, detail="Task not found")
    return artifact.model_dump(mode="json")


@router.get("/{task_id}/artifacts")
async def list_artifacts(task_id: str):
    mgr = get_mgr()
    artifacts = mgr.list_artifacts(task_id)
    return {"artifacts": [a.model_dump(mode="json") for a in artifacts], "count": len(artifacts)}


@router.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    mgr = get_mgr()
    artifact = mgr.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact.model_dump(mode="json")


@router.get("/artifacts/{artifact_id}/download")
async def download_artifact(artifact_id: str):
    mgr = get_mgr()
    artifact = mgr.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    for part in artifact.parts:
        if part.type == PartType.FILE and part.file_uri and os.path.isfile(part.file_uri):
            with open(part.file_uri, "rb") as f:
                content = f.read()
            media_type = part.content_type or "application/octet-stream"
            filename = part.filename or "artifact"
            return Response(content=content, media_type=media_type,
                            headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    return artifact.model_dump(mode="json")


@router.get("/{task_id}/summary")
async def get_task_summary(task_id: str):
    mgr = get_mgr()
    summary = mgr.get_task_summary(task_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Task not found")
    return summary


# ─── Context ──────────────────────────────────────────────────────


@router.post("/context", status_code=201)
async def create_context(agent_id: str = "hasha2a", parent_context_id: str | None = None):
    ctx = get_ctx()
    context = ctx.create_context(agent_id=agent_id, parent_context_id=parent_context_id)
    return context.model_dump(mode="json")


@router.get("/context/{context_id}")
async def get_context(context_id: str):
    ctx = get_ctx()
    context = ctx.get_context(context_id)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    return context.model_dump(mode="json")


@router.get("/context/{context_id}/summary")
async def get_context_summary(context_id: str):
    ctx = get_ctx()
    summary = ctx.get_compact_summary(context_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Context not found")
    return summary


@router.post("/context/{context_id}/fork")
async def fork_context(context_id: str):
    ctx = get_ctx()
    child = ctx.fork_context(context_id)
    if not child:
        raise HTTPException(status_code=404, detail="Context not found")
    return child.model_dump(mode="json")


@router.get("/context/{context_id}/history")
async def get_context_history(context_id: str, limit: int = Query(20, ge=1, le=100)):
    ctx = get_ctx()
    history = ctx.get_interactions(context_id, limit=limit)
    return {"history": history, "count": len(history)}


@router.get("/contexts")
async def list_contexts(limit: int = Query(20, ge=1, le=100)):
    ctx = get_ctx()
    contexts = ctx.list_contexts(limit=limit)
    return {"contexts": [c.model_dump(mode="json") for c in contexts], "count": len(contexts)}
