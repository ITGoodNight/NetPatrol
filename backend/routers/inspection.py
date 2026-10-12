import os
import sys
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

# 确保根目录在路径中
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# 注入 Qt 兼容 Shim（防止 Inspector 因 PySide6 缺失而报错）
try:
    import PySide6  # noqa: F401
except ImportError:
    from backend.qt_compat import Signal, QObject
    import types as _types
    _m = _types.ModuleType("PySide6")
    _mc = _types.ModuleType("PySide6.QtCore")
    _mc.Signal = Signal
    _mc.QObject = QObject
    sys.modules.setdefault("PySide6", _m)
    sys.modules.setdefault("PySide6.QtCore", _mc)

from backend.ws_manager import manager
from backend import inspection_service
from backend.history_manager import list_history, clear_history
from backend.paths import REPORTS_DIR

router = APIRouter(prefix="/api/inspection", tags=["inspection"])

DEFAULT_RESULT_DIR = REPORTS_DIR


# ── 请求模型 ──────────────────────────────────────────────────────────────────
class StartInspectionRequest(BaseModel):
    devices: List[Dict[str, Any]]   # 前端传回的完整设备列表（含 _raw）
    max_workers: int = 10
    result_dir: Optional[str] = None
    output_format: str = "HTML"


# ── WebSocket 端点 ────────────────────────────────────────────────────────────
@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """实时日志推送 WebSocket"""
    await manager.connect(websocket)
    from backend.schedule_manager import load_config, format_schedule_status
    try:
        await websocket.send_json({
            "type": "log",
            "level": "INFO",
            "message": format_schedule_status(load_config()),
        })
    except Exception:
        pass
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ── HTTP 端点 ─────────────────────────────────────────────────────────────────
@router.post("/start")
async def start_inspection(req: StartInspectionRequest):
    """启动任务（在后台线程执行，不阻塞 HTTP 响应）"""
    if inspection_service.is_inspection_running():
        raise HTTPException(status_code=409, detail="当前任务正在运行中")

    real_devices = []
    for d in req.devices:
        raw = d.get("_raw")
        if raw:
            real_devices.append(raw)
        else:
            real_devices.append(d)

    if not real_devices:
        raise HTTPException(status_code=400, detail="设备列表为空")

    result_dir = req.result_dir or DEFAULT_RESULT_DIR
    launched = inspection_service.launch_inspection(
        devices=real_devices,
        max_workers=req.max_workers,
        output_format=req.output_format,
        result_dir=result_dir,
        source="manual",
    )
    if not launched:
        raise HTTPException(status_code=409, detail="当前任务正在运行中")

    return {"success": True, "message": f"巡检已启动，共 {len(real_devices)} 台设备"}


@router.post("/stop")
async def stop_inspection():
    """停止当前巡检任务"""
    if not inspection_service.stop_inspection():
        return {"success": False, "message": "当前没有正在运行的巡检任务"}
    return {"success": True, "message": "已发送停止信号"}


@router.get("/status")
async def get_status():
    """获取当前巡检进度"""
    running = inspection_service.is_inspection_running()
    insp = inspection_service.get_inspector()
    if insp:
        progress = insp.get_progress()
    else:
        progress = {"total": 0, "completed": 0, "successful": 0, "failed": 0}
    return {"success": True, "running": running, "progress": progress}


@router.get("/results")
async def list_results():
    """列出巡检结果文件"""
    if not os.path.exists(DEFAULT_RESULT_DIR):
        return {"success": True, "files": []}

    files = []
    for fname in sorted(os.listdir(DEFAULT_RESULT_DIR), reverse=True):
        if fname.endswith(('.html', '.txt')):
            fpath = os.path.join(DEFAULT_RESULT_DIR, fname)
            stat = os.stat(fpath)
            files.append({
                "name": fname,
                "size": stat.st_size,
                "modified": stat.st_mtime,
            })
    return {"success": True, "files": files}


@router.get("/results/{filename}")
async def get_result_file(filename: str, download: bool = False):
    """获取/下载单个结果文件（默认 inline 预览，download=1 时触发下载）"""
    result_dir = os.path.abspath(DEFAULT_RESULT_DIR)
    file_path = os.path.join(result_dir, filename)

    if not os.path.abspath(file_path).startswith(result_dir):
        raise HTTPException(status_code=400, detail="非法路径")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    media_type = "text/html" if filename.endswith('.html') else "text/plain"
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=filename,
        content_disposition_type="attachment" if download else "inline",
    )


@router.delete("/results/{filename}")
async def delete_result_file(filename: str):
    """删除单个结果文件"""
    result_dir = os.path.abspath(DEFAULT_RESULT_DIR)
    file_path = os.path.join(result_dir, filename)

    if not os.path.abspath(file_path).startswith(result_dir):
        raise HTTPException(status_code=400, detail="非法路径")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        os.remove(file_path)
        return {"success": True, "message": f"文件 {filename} 删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {e}")


@router.get("/history")
async def get_inspection_history():
    """获取巡检执行历史"""
    return {"success": True, "records": list_history()}


@router.delete("/history")
async def delete_inspection_history():
    """清空巡检执行历史"""
    count = clear_history()
    return {"success": True, "message": f"已清空 {count} 条历史记录"}


@router.delete("/results")
async def clear_all_results():
    """清空所有巡检结果文件"""
    result_dir = os.path.abspath(DEFAULT_RESULT_DIR)
    if not os.path.exists(result_dir):
        return {"success": True, "message": "目录不存在"}

    deleted_count = 0
    try:
        for fname in os.listdir(result_dir):
            if fname.endswith(('.html', '.txt')):
                fpath = os.path.join(result_dir, fname)
                os.remove(fpath)
                deleted_count += 1
        return {"success": True, "message": f"成功清空 {deleted_count} 个结果文件"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空结果文件失败: {e}")
