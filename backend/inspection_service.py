"""
巡检任务启动服务（手动 / 定时共用）
"""
import os
import json
import asyncio
import threading
from typing import List, Dict, Any, Optional

from modules.inspector import Inspector
from modules.config_loader import ConfigLoader
from backend.ws_manager import manager
from backend.history_manager import append_history
from backend.paths import COMMANDS_PATH, APP_CONFIG_PATH, REPORTS_DIR

DEFAULT_RESULT_DIR = REPORTS_DIR

_inspector: Optional[Inspector] = None
_inspection_running = False
_inspection_lock = threading.Lock()
_user_stopped = False


def is_inspection_running() -> bool:
    with _inspection_lock:
        return _inspection_running


def get_inspector() -> Optional[Inspector]:
    with _inspection_lock:
        return _inspector


def stop_inspection() -> bool:
    global _inspector, _inspection_running, _user_stopped
    with _inspection_lock:
        if not _inspection_running or _inspector is None:
            return False
        _user_stopped = True
        _inspector.stop_inspection()
    return True


def clear_stop_flag() -> None:
    global _user_stopped
    with _inspection_lock:
        _user_stopped = False


def was_stop_requested() -> bool:
    with _inspection_lock:
        return _user_stopped


def _normalize_devices(devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    real_devices = []
    for d in devices:
        raw = d.get("_raw")
        if raw:
            real_devices.append(raw)
        else:
            real_devices.append(d)
    return real_devices


def _load_retry_count() -> int:
    try:
        with open(APP_CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return max(0, min(int(data.get("retry_count", 0)), 3))
    except Exception:
        return 0


def _device_key(device: Dict[str, Any]) -> str:
    return f"{device.get('设备名称', '')}|{device.get('IP地址', '')}"


def _retry_failed_devices(insp: Inspector, max_retries: int, source_label: str, emit_progress) -> tuple:
    """对失败设备重试，返回 (实际重试轮数, 挽回成功台数)"""
    recovered = 0
    actual_rounds = 0
    if max_retries <= 0:
        return actual_rounds, recovered

    for round_num in range(1, max_retries + 1):
        failed_items = [r for r in insp.results if r.get("status") == "failed"]
        if not failed_items:
            break

        actual_rounds = round_num
        manager.broadcast_sync(
            "INFO",
            f"[{source_label}] 失败重试 {round_num}/{max_retries}：{len(failed_items)} 台设备",
        )

        for item in failed_items:
            if insp._stop_event.is_set():
                return actual_rounds, recovered

            device = item["device"]
            with insp._lock:
                insp.failed_devices = max(0, insp.failed_devices - 1)
                insp.completed_devices = max(0, insp.completed_devices - 1)

            result = insp._inspect_device(device)

            for i, r in enumerate(insp.results):
                if _device_key(r.get("device", {})) == _device_key(device):
                    if r.get("status") == "failed" and result.get("status") == "success":
                        recovered += 1
                    insp.results[i] = result
                    break

            emit_progress()

    return actual_rounds, recovered


def launch_inspection(
    devices: List[Dict[str, Any]],
    max_workers: int = 10,
    output_format: str = "HTML",
    result_dir: Optional[str] = None,
    source: str = "manual",
) -> bool:
    """
    在后台线程启动巡检。若已有任务运行中则返回 False。
    """
    global _inspector, _inspection_running

    real_devices = _normalize_devices(devices)
    if not real_devices:
        manager.broadcast_sync("WARNING", "定时巡检跳过：设备列表为空，请先添加设备")
        return False

    try:
        loader = ConfigLoader(COMMANDS_PATH)
        config = loader.load_config()
    except Exception as e:
        manager.broadcast_sync("ERROR", f"加载命令配置失败: {e}")
        return False

    with _inspection_lock:
        if _inspection_running:
            manager.broadcast_sync("WARNING", "定时巡检跳过：当前已有巡检任务正在运行")
            return False
        _inspection_running = True

    target_dir = result_dir or DEFAULT_RESULT_DIR
    source_label = "定时任务" if source == "schedule" else "手动任务"
    retry_count = _load_retry_count()

    def run_inspection():
        global _inspector, _inspection_running

        actual_retry_rounds = 0
        retry_recovered = 0

        try:
            insp = Inspector(
                max_workers=max_workers,
                result_dir=target_dir,
                output_format=output_format,
            )
            insp.set_log_callback(lambda level, msg: manager.broadcast_sync(level, msg))

            with _inspection_lock:
                _inspector = insp

            def emit_progress():
                p = insp.get_progress()
                manager.broadcast_progress_sync(
                    p["total"], p["completed"], p["successful"], p["failed"]
                )

            original_inspect = insp._inspect_device

            def wrapped_inspect(device):
                result = original_inspect(device)
                emit_progress()
                return result

            insp._inspect_device = wrapped_inspect

            start_msg = (
                f"[{source_label}] 开始执行，共 {len(real_devices)} 台设备，"
                f"并发线程: {max_workers}，输出格式: {output_format}"
            )
            if retry_count:
                start_msg += f"，失败重试: {retry_count} 次"
            manager.broadcast_sync("INFO", start_msg)
            insp.start_inspection(real_devices, config)

            if retry_count > 0 and not insp._stop_event.is_set() and insp.failed_devices > 0:
                actual_retry_rounds, retry_recovered = _retry_failed_devices(
                    insp, retry_count, source_label, emit_progress
                )

            p = insp.get_progress()
            emit_progress()

            record = append_history(
                source=source,
                total=p["total"],
                successful=p["successful"],
                failed=p["failed"],
                retry_rounds=actual_retry_rounds,
                retry_recovered=retry_recovered,
            )

            summary = f"[{source_label}] 执行完成：成功 {p['successful']} 台，失败 {p['failed']} 台"
            if retry_recovered:
                summary += f"，重试挽回 {retry_recovered} 台"
            manager.broadcast_sync("SUCCESS", summary)

            if manager._loop and not manager._loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast({"type": "finished", "history": record}), manager._loop
                )
        except Exception as e:
            manager.broadcast_sync("ERROR", f"[{source_label}] 巡检异常终止: {e}")
        finally:
            with _inspection_lock:
                _inspection_running = False

    thread = threading.Thread(target=run_inspection, daemon=True)
    thread.start()
    return True
