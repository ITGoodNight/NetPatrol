"""
设备清单相关 API 路由
"""
import os
import sys
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException

# 确保可以 import modules/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from modules.device_parser import DeviceParser

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.post("/upload")
async def upload_device_list(file: UploadFile = File(...)):
    """
    上传设备清单 Excel 文件，返回解析后的设备列表
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="仅支持 Excel 文件 (.xlsx/.xls)")

    # 将上传文件保存到临时目录
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        parser = DeviceParser(tmp_path)
        devices = parser.parse_devices()

        # 返回时隐藏密码
        safe_devices = []
        for d in devices:
            safe_devices.append({
                "设备名称": d.get("设备名称", ""),
                "设备类型": d.get("设备类型", ""),
                "IP地址": d.get("IP地址", ""),
                "端口号": d.get("端口号", ""),
                "连接类型": d.get("连接类型", ""),
                "用户名": d.get("用户名", ""),
                "密码": "*" * len(d.get("密码", "")),
                "_raw": d,  # 内部保留原始数据（不暴露到前端显示用）
            })
        return {"success": True, "count": len(devices), "devices": safe_devices}
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


from typing import Dict, Any

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
