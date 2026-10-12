"""
NetPatrol FastAPI 后端主入口

启动方式：
    uvicorn backend.main_api:app --host 0.0.0.0 --port 8000 --reload
或直接运行：
    python backend/main_api.py
"""
import os
import sys
import asyncio

# 确保项目根目录在 Python 路径中
if getattr(sys, 'frozen', False):
    ROOT_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

# ── 注入 Qt 兼容 Shim（在 PySide6 未安装时提供替代实现）──────────────────
# 必须在 modules.inspector 被 import 之前执行
try:
    import PySide6  # noqa: F401
except ImportError:
    # PySide6 未安装 → 注入纯 Python 兼容实现到 sys.modules
    from backend.qt_compat import Signal, QObject
    import types
    _fake_pyside6 = types.ModuleType("PySide6")
    _fake_qtcore = types.ModuleType("PySide6.QtCore")
    _fake_qtcore.Signal = Signal
    _fake_qtcore.QObject = QObject
    sys.modules["PySide6"] = _fake_pyside6
    sys.modules["PySide6.QtCore"] = _fake_qtcore

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.routers import devices, inspection, config, settings, network_test
from backend.ws_manager import manager
from backend.schedule_manager import schedule_manager
from backend.paths import migrate_legacy_config_files, ensure_runtime_dirs, FRONTEND_DIST

# ── 创建 FastAPI 应用 ─────────────────────────────────────────────────────────
app = FastAPI(
    title="NetPatrol API",
    description="网络设备自动化巡检系统 Web 后端",
    version="2.0.0",
)

# ── CORS（开发阶段允许所有来源，生产由 Nginx 控制）───────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ──────────────────────────────────────────────────────────────────
app.include_router(devices.router)
app.include_router(inspection.router)
app.include_router(config.router)
app.include_router(settings.router)
app.include_router(network_test.router)

# WebSocket 路由（在 inspection 路由中定义，但需要从顶层挂载）
# inspection.router 内已包含 /api/inspection/ws/logs

# ── 启动事件：记录事件循环供 WebSocket 广播使用 ────────────────────────────
@app.on_event("startup")
async def on_startup():
    ensure_runtime_dirs()
    migrate_legacy_config_files()
    manager.set_loop(asyncio.get_running_loop())
    await schedule_manager.start()


@app.on_event("shutdown")
async def on_shutdown():
    await schedule_manager.stop()



# ── 静态文件服务（前端构建产物）────────────────────────────────────────────
FRONTEND_DIST_PATH = FRONTEND_DIST

if os.path.exists(FRONTEND_DIST_PATH):
    # 挂载静态资源（CSS/JS/图片等）
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST_PATH, "assets")), name="assets")
    app.mount("/icons", StaticFiles(directory=os.path.join(FRONTEND_DIST_PATH, "icons")), name="icons")

    @app.get("/", response_class=FileResponse)
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIST_PATH, "index.html"))

    @app.get("/{full_path:path}", response_class=FileResponse)
    async def serve_spa(full_path: str):
        """SPA 路由回退：所有非 API 路由都返回 index.html"""
        file_path = os.path.join(FRONTEND_DIST_PATH, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST_PATH, "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "message": "NetPatrol API 运行中",
            "hint": "前端未构建，请运行 cd frontend && npm run build",
            "docs": "/docs"
        }


# ── 直接运行 ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main_api:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
