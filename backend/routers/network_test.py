"""
网络测试 API：Ping 持续探测 / Tracert 路由追踪
"""
import asyncio
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.network_utils import ping_once, stream_tracert, validate_target

router = APIRouter(prefix="/api/network", tags=["network"])


@router.websocket("/ws/test")
async def websocket_network_test(websocket: WebSocket):
    await websocket.accept()
    ping_task: Optional[asyncio.Task] = None
    tracert_task: Optional[asyncio.Task] = None
    ping_stop = asyncio.Event()

    async def stop_ping():
        nonlocal ping_task
        ping_stop.set()
        if ping_task and not ping_task.done():
            ping_task.cancel()
            try:
                await ping_task
            except asyncio.CancelledError:
                pass
        ping_task = None
        ping_stop.clear()

    async def stop_tracert():
        nonlocal tracert_task
        if tracert_task and not tracert_task.done():
            tracert_task.cancel()
            try:
                await tracert_task
            except asyncio.CancelledError:
                pass
        tracert_task = None

    async def run_ping_loop(target: str, interval: float):
        seq = 0
        try:
            while not ping_stop.is_set():
                seq += 1
                latency, status, _ = await ping_once(target)
                await websocket.send_json({
                    "type": "ping",
                    "seq": seq,
                    "latency_ms": latency,
                    "status": status,
                })
                try:
                    await asyncio.wait_for(ping_stop.wait(), timeout=max(0.5, interval))
                    break
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            pass
        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})

    async def run_tracert(target: str, max_hops: int):
        try:
            await websocket.send_json({"type": "tracert_start", "target": target})
            async for line in stream_tracert(target, max_hops):
                await websocket.send_json({"type": "tracert_line", "line": line})
            await websocket.send_json({"type": "tracert_done", "success": True})
        except asyncio.CancelledError:
            await websocket.send_json({"type": "tracert_done", "success": False, "cancelled": True})
        except Exception as e:
            await websocket.send_json({"type": "error", "message": str(e)})
            await websocket.send_json({"type": "tracert_done", "success": False})

    try:
        while True:
            raw = await websocket.receive_text()
            if raw == 'ping':
                await websocket.send_json({"type": "pong"})
                continue

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "无效的消息格式"})
                continue

            action = data.get("action")

            if action == "ping_start":
                await stop_tracert()
                await stop_ping()
                try:
                    target = validate_target(data.get("target", ""))
                except ValueError as e:
                    await websocket.send_json({"type": "error", "message": str(e)})
                    continue
                interval = float(data.get("interval", 1))
                interval = max(0.5, min(interval, 10))
                ping_task = asyncio.create_task(run_ping_loop(target, interval))
                await websocket.send_json({"type": "ping_started", "target": target, "interval": interval})

            elif action == "ping_stop":
                await stop_ping()
                await websocket.send_json({"type": "ping_stopped"})

            elif action == "tracert":
                await stop_ping()
                await stop_tracert()
                try:
                    target = validate_target(data.get("target", ""))
                except ValueError as e:
                    await websocket.send_json({"type": "error", "message": str(e)})
                    continue
                max_hops = int(data.get("max_hops", 30))
                tracert_task = asyncio.create_task(run_tracert(target, max_hops))

            elif action == "stop":
                await stop_ping()
                await stop_tracert()
                await websocket.send_json({"type": "stopped"})

    except WebSocketDisconnect:
        pass
    finally:
        await stop_ping()
        await stop_tracert()
