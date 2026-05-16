"""A2A Context & Memory — context IDs, interaction history, and summaries."""

import time
import uuid
from typing import Any

from models.schemas import ContextSummary


class ContextManager:
    """Manages A2A context: keeps interaction history and generates summaries
    that can be passed between agents without sharing full memory."""

    def __init__(self, max_history: int = 50):
        self._contexts: dict[str, ContextSummary] = {}
        self._interactions: dict[str, list[dict[str, Any]]] = {}
        self._max_history = max_history

    def create_context(self, agent_id: str = "hasha2a", parent_context_id: str | None = None) -> ContextSummary:
        ctx = ContextSummary(
            context_id=str(uuid.uuid4()),
            agent_id=agent_id,
            parent_context_id=parent_context_id,
        )
        self._contexts[ctx.context_id] = ctx
        self._interactions[ctx.context_id] = []
        return ctx

    def get_context(self, context_id: str) -> ContextSummary | None:
        return self._contexts.get(context_id)

    def add_interaction(self, context_id: str, task_id: str, summary: str, metadata: dict | None = None) -> bool:
        ctx = self._contexts.get(context_id)
        if not ctx:
            return False
        ctx.interaction_count += 1
        ctx.last_task_ids.append(task_id)
        if len(ctx.last_task_ids) > 10:
            ctx.last_task_ids = ctx.last_task_ids[-10:]
        ctx.summary = self._merge_summaries(ctx.summary, summary)
        ctx.updated_at = int(time.time())
        self._interactions[context_id].append({
            "task_id": task_id,
            "summary": summary,
            "metadata": metadata or {},
            "timestamp": int(time.time()),
        })
        if len(self._interactions[context_id]) > self._max_history:
            self._interactions[context_id] = self._interactions[context_id][-self._max_history:]
        return True

    def get_interactions(self, context_id: str, limit: int = 20) -> list[dict]:
        history = self._interactions.get(context_id, [])
        return history[-limit:]

    def get_summary(self, context_id: str) -> str | None:
        ctx = self._contexts.get(context_id)
        if not ctx:
            return None
        return ctx.summary

    def get_compact_summary(self, context_id: str) -> dict | None:
        ctx = self._contexts.get(context_id)
        if not ctx:
            return None
        return {
            "context_id": ctx.context_id,
            "parent_context_id": ctx.parent_context_id,
            "agent_id": ctx.agent_id,
            "summary": ctx.summary[:500],
            "interaction_count": ctx.interaction_count,
            "recent_tasks": ctx.last_task_ids[-3:],
            "updated_at": ctx.updated_at,
        }

    def fork_context(self, context_id: str) -> ContextSummary | None:
        parent = self._contexts.get(context_id)
        if not parent:
            return None
        child = self.create_context(
            agent_id=parent.agent_id,
            parent_context_id=context_id,
        )
        child.summary = parent.summary
        child.interaction_count = parent.interaction_count
        return child

    def list_contexts(self, limit: int = 20) -> list[ContextSummary]:
        contexts = sorted(
            self._contexts.values(),
            key=lambda c: c.updated_at,
            reverse=True,
        )
        return contexts[:limit]

    def _merge_summaries(self, existing: str, new: str) -> str:
        if not existing:
            return new
        combined = f"{existing} | {new}"
        if len(combined) > 2000:
            return combined[-2000:]
        return combined
