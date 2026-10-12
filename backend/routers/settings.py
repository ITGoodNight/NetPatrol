"""
系统设置相关 API 路由
"""
import os
import sys
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.ws_manager import manager
from backend.schedule_manager import format_schedule_status
from backend.paths import APP_CONFIG_PATH, ensure_config_dir

router = APIRouter(prefix="/api/settings", tags=["settings"])

AI_CONFIG_PATH = APP_CONFIG_PATH

DEFAULT_CONFIG = {
    "output_format": "HTML",
    "enable_schedule": False,
    "schedule_mode": "daily",
    "schedule_time": "09:00",
    "schedule_date": "",
    "schedule_count": 1,
    "max_workers": 10,
    "retry_count": 0,
    "enable_result_notify": False,
    "schedule_devices": [],
}


def _load_ai_config() -> dict:
    try:
        with open(AI_CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {**DEFAULT_CONFIG, **data}
    except FileNotFoundError:
        return DEFAULT_CONFIG.copy()
    except Exception as e:
        raise Exception(f"加载配置失败: {e}")


def _save_ai_config(config: dict):
    ensure_config_dir()
    with open(AI_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


@router.get("/ai")
async def get_ai_settings():
    """获取配置"""
    try:
        config = _load_ai_config()
        return {"success": True, "config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AISettingsPayload(BaseModel):
    output_format: str
    enable_schedule: bool
    schedule_mode: str
    schedule_time: str
    schedule_date: Optional[str] = ""
    schedule_count: Optional[int] = 1
    max_workers: Optional[int] = 10
    retry_count: Optional[int] = 0
    enable_result_notify: Optional[bool] = False
    schedule_devices: Optional[List[Dict[str, Any]]] = None


@router.post("/ai")
async def save_ai_settings(payload: AISettingsPayload):
    """保存系统配置"""
    try:
        config = _load_ai_config()
        data = payload.model_dump()
        if data.get("schedule_devices") is None:
            data.pop("schedule_devices", None)
        config.update(data)
        try:
            config["schedule_count"] = max(1, min(int(config.get("schedule_count") or 1), 24))
        except (TypeError, ValueError):
            config["schedule_count"] = 1
        _save_ai_config(config)
        manager.broadcast_sync("INFO", f"定时巡检设置已更新 | {format_schedule_status(config)}")
        return {"success": True, "message": "设置已保存", "config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
