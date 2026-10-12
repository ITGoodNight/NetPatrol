"""
WebSocket 连接管理器：负责广播实时巡检日志到所有连接的前端客户端
"""
import asyncio
from typing import List
from fastapi import WebSocket


class ConnectionManager:
    """管理所有活跃的 WebSocket 连接，负责日志广播"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """异步广播消息到所有连接"""
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def broadcast_sync(self, level: str, message: str):
        """
        从同步线程（巡检工作线程）安全地广播日志
        通过 call_soon_threadsafe 把协程投递到事件循环
        """
        if self._loop and not self._loop.is_closed():
            payload = {"type": "log", "level": level, "message": message}
            asyncio.run_coroutine_threadsafe(self.broadcast(payload), self._loop)

    def broadcast_progress_sync(self, total: int, completed: int, successful: int, failed: int):
        """从同步线程广播进度更新"""
        if self._loop and not self._loop.is_closed():
            payload = {
                "type": "progress",
                "total": total,
                "completed": completed,
                "successful": successful,
                "failed": failed,
            }
            asyncio.run_coroutine_threadsafe(self.broadcast(payload), self._loop)


# 全局单例
manager = ConnectionManager()
