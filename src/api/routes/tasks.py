"""A2A-compatible Task API — lifecycle, artifacts, and status."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Any

from core.task_manager import TaskManager
from models.schemas import (
    TaskObject, TaskStatus, MessagePart, PartType, Artifact,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])

_task_mgr: TaskManager | None = None


def get_mgr() -> TaskManager:
    global _task_mgr
    if _task_mgr is None:
        _task_mgr = TaskManager()
    return _task_mgr


@router.post("", status_code=201)
async def create_task(
    agent_id: str = "hasha2a",
    context_id: str | None = None,
):
    mgr = get_mgr()
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
    return {
        "status": "completed",
        "artifact": artifact.model_dump(mode="json"),
    }


@router.post("/{task_id}/artifacts", status_code=201)
async def add_artifact(task_id: str, parts: list[MessagePart]):
    mgr = get_mgr()
    artifact = mgr.add_artifact(task_id, parts)
    if not artifact:
        raise HTTPException(status_code=404, detail="Task not found")
    return artifact.model_dump(mode="json")


@router.get("/{task_id}/artifacts")
async def list_artifacts(task_id: str):
    mgr = get_mgr()
    artifacts = mgr.list_artifacts(task_id)
    return {
        "artifacts": [a.model_dump(mode="json") for a in artifacts],
        "count": len(artifacts),
    }


@router.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    mgr = get_mgr()
    artifact = mgr.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact.model_dump(mode="json")


@router.get("/{task_id}/summary")
async def get_task_summary(task_id: str):
    mgr = get_mgr()
    summary = mgr.get_task_summary(task_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Task not found")
    return summary
