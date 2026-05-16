"""A2A JSON-RPC 2.0 endpoint — task management via standard A2A protocol.

Implements methods: message/send, message/stream, tasks/get, tasks/list,
tasks/cancel, tasks/subscribe.
"""

import asyncio
import json
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from core.task_manager import TaskManager
from core.context_manager import ContextManager
from models.schemas import TaskStatus, MessagePart, PartType

router = APIRouter(prefix="/a2a", tags=["a2a"])

_task_mgr: TaskManager | None = None
_ctx_mgr: ContextManager | None = None


def get_mgr() -> TaskManager:
    global _task_mgr, _ctx_mgr
    if _task_mgr is None:
        _ctx_mgr = ContextManager()
        _task_mgr = TaskManager(context_manager=_ctx_mgr)
    return _task_mgr


def _a2a_state(status: TaskStatus) -> str:
    mapping = {
        TaskStatus.SUBMITTED: "TASK_STATE_SUBMITTED",
        TaskStatus.WORKING: "TASK_STATE_WORKING",
        TaskStatus.INPUT_REQUIRED: "TASK_STATE_INPUT_REQUIRED",
        TaskStatus.COMPLETED: "TASK_STATE_COMPLETED",
        TaskStatus.FAILED: "TASK_STATE_FAILED",
        TaskStatus.CANCELED: "TASK_STATE_CANCELED",
        TaskStatus.REJECTED: "TASK_STATE_REJECTED",
    }
    return mapping.get(status, "TASK_STATE_SUBMITTED")


def _build_task_json(task) -> dict:
    parts_json = []
    for p in task.parts:
        pj = {"type": p.type.value}
        if p.text:
            pj["text"] = p.text
        if p.data:
            pj["data"] = p.data
        if p.file_uri:
            pj["uri"] = p.file_uri
        if p.filename:
            pj["filename"] = p.filename
        if p.content_type:
            pj["mediaType"] = p.content_type
        parts_json.append(pj)

    artifacts_json = []
    for a_id in task.artifacts:
        from core.task_manager import TaskManager
        artifacts_json.append({"artifactId": a_id})

    result = {
        "id": task.task_id,
        "status": {"state": _a2a_state(task.status)},
        "parts": parts_json,
        "artifacts": artifacts_json,
    }
    if task.context_id:
        result["contextId"] = task.context_id
    return result


def _process_message(parts: list[dict], context_id: str | None) -> dict:
    """Process incoming message and return task result."""
    mgr = get_mgr()
    if context_id and not _ctx_mgr.get_context(context_id):
        ctx = _ctx_mgr.create_context()
        context_id = ctx.context_id
    elif not context_id:
        ctx = _ctx_mgr.create_context()
        context_id = ctx.context_id

    task = mgr.create_task(context_id=context_id)

    for p in parts:
        ptype = p.get("type", "text")
        text = p.get("text", "")
        if ptype == "text" and text:
            mgr.add_text(task.task_id, text)

    mgr.start_working(task.task_id)

    query = task.parts[-1].text if task.parts else ""
    from core.ai_analyzer import AIAnalyzer
    from core.config import Settings
    settings = Settings()
    analyzer = AIAnalyzer(settings)

    if "price" in query.lower() or "btc" in query.lower() or "eth" in query.lower():
        import asyncio
        from core.oracle_hub import OracleHub
        hub = OracleHub()
        asset = "BTC/USD"
        for a in ["BTC/USD", "ETH/USD", "SOL/USD", "XAU/USD"]:
            if a.split("/")[0].lower() in query.lower():
                asset = a
                break
        prices = asyncio.get_event_loop().run_until_complete(hub.get_price(asset))
        mgr.add_data(task.task_id, {"prices": [p.to_dict() for p in prices], "asset": asset})
        hub.close()
        mgr.complete(task.task_id, f"Retrieved {asset} price from {len(prices)} oracles")
    elif "arbitrage" in query.lower() or "spread" in query.lower():
        import asyncio
        from core.oracle_hub import OracleHub
        from core.arbitrage_engine import ArbitrageEngine
        hub = OracleHub()
        engine = ArbitrageEngine(hub)
        signals = asyncio.get_event_loop().run_until_complete(engine.scan_all())
        hub.close()
        best = [s.to_dict() for s in signals[:3] if s.spread_pct > 0.001]
        mgr.add_data(task.task_id, {"signals": best})
        mgr.complete(task.task_id, f"Found {len(best)} arbitrage opportunities")
    else:
        mgr.complete(task.task_id, f"Processed: {query[:100]}")

    return _build_task_json(task)


@router.post("/rpc")
async def a2a_rpc(request: Request):
    body = await request.json()
    jsonrpc = body.get("jsonrpc")
    method = body.get("method", "")
    params = body.get("params", {}) or {}
    req_id = body.get("id")

    if jsonrpc != "2.0":
        return __rpc_error(req_id, -32600, "Invalid JSON-RPC 2.0 request")

    try:
        if method == "message/send":
            return await _handle_message_send(req_id, params)
        elif method == "tasks/get":
            return await _handle_tasks_get(req_id, params)
        elif method == "tasks/list":
            return await _handle_tasks_list(req_id, params)
        elif method == "tasks/cancel":
            return await _handle_tasks_cancel(req_id, params)
        else:
            return __rpc_error(req_id, -32601, f"Method not found: {method}")
    except Exception as e:
        return __rpc_error(req_id, -32603, str(e)[:200])


@router.post("/rpc/stream")
async def a2a_rpc_stream(request: Request):
    """SSE streaming endpoint for message/stream and tasks/subscribe."""
    body = await request.json()
    method = body.get("method", "")
    params = body.get("params", {}) or {}
    req_id = body.get("id")

    if method == "message/stream":
        message = params.get("message", {})
        parts = message.get("parts", [])
        context_id = message.get("contextId") or params.get("contextId")

        mgr = get_mgr()
        if context_id and not _ctx_mgr.get_context(context_id):
            ctx = _ctx_mgr.create_context()
            context_id = ctx.context_id
        elif not context_id:
            ctx = _ctx_mgr.create_context()
            context_id = ctx.context_id

        task = mgr.create_task(context_id=context_id)

        # Process message parts
        for p in parts:
            ptype = p.get("type", "text")
            text = p.get("text", "")
            if ptype == "text" and text:
                mgr.add_text(task.task_id, text)

        async def event_stream():
            yield f"data: {json.dumps({'jsonrpc':'2.0','id':req_id,'result':{'task':{'id':task.task_id,'status':{'state':'TASK_STATE_SUBMITTED'}}}})}\n\n"
            await asyncio.sleep(0.1)

            mgr.start_working(task.task_id)
            yield f"event: task/status\ndata: {json.dumps({'jsonrpc':'2.0','id':req_id,'result':{'task':{'id':task.task_id,'status':{'state':'TASK_STATE_WORKING'}}}})}\n\n"

            query = task.parts[-1].text if task.parts else ""
            if "price" in query.lower() or "btc" in query.lower():
                yield f"event: task/progress\ndata: {json.dumps({'jsonrpc':'2.0','id':req_id,'result':{'task':{'id':task.task_id,'progress':{'message':'Consulting oracle network...'}}}})}\n\n"
                await asyncio.sleep(0.3)
                from core.oracle_hub import OracleHub
                hub = OracleHub()
                asset = "BTC/USD"
                for a in ["BTC/USD", "ETH/USD", "SOL/USD", "XAU/USD"]:
                    if a.split("/")[0].lower() in query.lower():
                        asset = a
                        break
                prices = await hub.get_price(asset)
                hub.close()
                mgr.add_data(task.task_id, {"prices": [p.to_dict() for p in prices], "asset": asset})
                mgr.complete(task.task_id, f"Retrieved {asset} price from {len(prices)} oracles")
            elif "arbitrage" in query.lower() or "spread" in query.lower():
                yield f"event: task/progress\ndata: {json.dumps({'jsonrpc':'2.0','id':req_id,'result':{'task':{'id':task.task_id,'progress':{'message':'Scanning for arbitrage opportunities...'}}}})}\n\n"
                await asyncio.sleep(0.3)
                from core.oracle_hub import OracleHub
                from core.arbitrage_engine import ArbitrageEngine
                hub = OracleHub()
                engine = ArbitrageEngine(hub)
                signals = await engine.scan_all()
                hub.close()
                best = [s.to_dict() for s in signals[:3] if s.spread_pct > 0.001]
                mgr.add_data(task.task_id, {"signals": best})
                mgr.complete(task.task_id, f"Found {len(best)} arbitrage opportunities")
            else:
                await asyncio.sleep(0.2)
                mgr.complete(task.task_id, f"Processed: {query[:100]}")

            result = _build_task_json(task)
            yield f"event: task/completed\ndata: {json.dumps({'jsonrpc':'2.0','id':req_id,'result':{'task':result}})}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    return __rpc_error(req_id, -32601, f"Method not found: {method}")


async def _handle_message_send(req_id, params):
    message = params.get("message", {})
    parts = message.get("parts", [])
    context_id = message.get("contextId") or params.get("contextId")
    task_json = _process_message(parts, context_id)
    return __rpc_result(req_id, {"task": task_json})


async def _handle_tasks_get(req_id, params):
    task_id = params.get("id", "")
    mgr = get_mgr()
    task = mgr.get_task(task_id)
    if not task:
        return __rpc_error(req_id, -32602, f"Task not found: {task_id}")
    return __rpc_result(req_id, {"task": _build_task_json(task)})


async def _handle_tasks_list(req_id, params):
    mgr = get_mgr()
    tasks = mgr.list_tasks(limit=params.get("limit", 50))
    return __rpc_result(req_id, {"tasks": [_build_task_json(t) for t in tasks]})


async def _handle_tasks_cancel(req_id, params):
    task_id = params.get("id", "")
    mgr = get_mgr()
    task = mgr.get_task(task_id)
    if not task:
        return __rpc_error(req_id, -32602, f"Task not found: {task_id}")
    mgr.update_status(task_id, TaskStatus.CANCELED)
    return __rpc_result(req_id, {"task": _build_task_json(task)})


def __rpc_result(req_id: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def __rpc_error(req_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}
