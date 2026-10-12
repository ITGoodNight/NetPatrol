"""
设备清单相关 API 路由
"""
import os
import sys
from typing import Dict, Any

from fastapi import APIRouter

# 确保可以 import modules/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.post("/test-connect")
async def test_device_connection(payload: Dict[str, Any]):
    """
    测试单台设备的连接可达性
    """
    from modules.netmiko_handler import NetmikoHandler
    try:
        password = payload.get("密码", "")
        if password.startswith("*" * min(len(password), 1)) and len(password) > 0:
            return {"success": False, "message": "测试连接需要重新输入明文密码（安全保护机制）"}

        handler = NetmikoHandler(payload, read_timeout=10, max_retries=1)
        connected = handler.connect()
        if connected:
            handler.disconnect()
            return {"success": True, "message": "连接测试成功！"}
        else:
            return {"success": False, "message": "连接测试失败，请检查网络或协议设置"}
    except Exception as e:
        return {"success": False, "message": f"连接失败: {str(e)}"}
