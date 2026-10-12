"""
命令配置相关 API 路由
"""
import os
import sys
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.paths import COMMANDS_PATH, ensure_config_dir

router = APIRouter(prefix="/api/config", tags=["config"])

CONFIG_PATH = COMMANDS_PATH


@router.get("/commands")
async def get_commands():
    """获取当前 commands.txt 内容"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"success": True, "content": content}
    except FileNotFoundError:
        return {"success": True, "content": ""}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CommandsPayload(BaseModel):
    content: str


@router.post("/commands")
async def save_commands(payload: CommandsPayload):
    """保存 commands.txt 内容"""
    try:
        ensure_config_dir()
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            f.write(payload.content)
        return {"success": True, "message": "配置已保存"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



