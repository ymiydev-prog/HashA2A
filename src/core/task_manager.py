"""A2A Task Manager — lifecycle, artifacts, context, and history."""

import time
from typing import Any

from models.schemas import (
    TaskObject, TaskStatus, MessagePart, PartType, Artifact,
)


class TaskManager:
    """Manages A2A task lifecycle: submitted → working → completed/failed."""

    def __init__(self):
        self._tasks: dict[str, TaskObject] = {}
        self._artifacts: dict[str, Artifact] = {}

    def create_task(self, agent_id: str = "hasha2a", context_id: str | None = None) -> TaskObject:
        task = TaskObject(agent_id=agent_id, context_id=context_id, status=TaskStatus.SUBMITTED)
        self._tasks[task.task_id] = task
        return task

    def get_task(self, task_id: str) -> TaskObject | None:
        return self._tasks.get(task_id)

    def list_tasks(self, status: TaskStatus | None = None, limit: int = 50) -> list[TaskObject]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    def update_status(self, task_id: str, new_status: TaskStatus) -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.transition(new_status)
        return True

    def add_part(self, task_id: str, part: MessagePart) -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.add_part(part)
        return True

    def add_text(self, task_id: str, text: str, metadata: dict | None = None) -> bool:
        return self.add_part(task_id, MessagePart(
            type=PartType.TEXT, text=text, metadata=metadata,
        ))

    def add_data(self, task_id: str, data: dict[str, Any], metadata: dict | None = None) -> bool:
        return self.add_part(task_id, MessagePart(
            type=PartType.DATA, data=data, metadata=metadata,
        ))

    def start_working(self, task_id: str) -> bool:
        return self.update_status(task_id, TaskStatus.WORKING)

    def request_input(self, task_id: str, prompt: str) -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.transition(TaskStatus.INPUT_REQUIRED)
        self.add_text(task_id, prompt)
        return True

    def complete(self, task_id: str, summary: str | None = None) -> Artifact | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.transition(TaskStatus.COMPLETED)
        parts = [MessagePart(type=PartType.TEXT, text=summary or "Task completed")]
        artifact = Artifact(task_id=task_id, parts=parts)
        self._artifacts[artifact.artifact_id] = artifact
        task.add_artifact_id(artifact.artifact_id)
        return artifact

    def fail(self, task_id: str, error: str) -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        self.add_text(task_id, f"Error: {error}")
        task.transition(TaskStatus.FAILED)
        return True

    def add_artifact(self, task_id: str, parts: list[MessagePart]) -> Artifact | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        artifact = Artifact(task_id=task_id, parts=parts)
        self._artifacts[artifact.artifact_id] = artifact
        task.add_artifact_id(artifact.artifact_id)
        return artifact

    def get_artifact(self, artifact_id: str) -> Artifact | None:
        return self._artifacts.get(artifact_id)

    def list_artifacts(self, task_id: str) -> list[Artifact]:
        task = self._tasks.get(task_id)
        if not task:
            return []
        return [self._artifacts[a_id] for a_id in task.artifacts if a_id in self._artifacts]

    def get_task_summary(self, task_id: str) -> dict[str, Any] | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        artifacts_summary = []
        for a_id in task.artifacts:
            art = self._artifacts.get(a_id)
            if art:
                artifacts_summary.append({
                    "artifact_id": art.artifact_id,
                    "parts": len(art.parts),
                    "created_at": art.created_at,
                })
        return {
            "task_id": task.task_id,
            "agent_id": task.agent_id,
            "status": task.status.value,
            "parts_count": len(task.parts),
            "artifacts": artifacts_summary,
            "context_id": task.context_id,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }

    def count_by_status(self) -> dict[str, int]:
        counts = {}
        for t in self._tasks.values():
            k = t.status.value
            counts[k] = counts.get(k, 0) + 1
        return counts
