"""
定时巡检调度器：读取 config.json，到点自动触发巡检
"""
import asyncio
import json
import os
import threading
import time
from datetime import datetime
from typing import Optional

from backend.ws_manager import manager
from backend.inspection_service import (
    launch_inspection,
    is_inspection_running,
    clear_stop_flag,
    was_stop_requested,
)

from backend.paths import APP_CONFIG_PATH as CONFIG_PATH

DEFAULT_CONFIG = {
    "output_format": "HTML",
    "enable_schedule": False,
    "schedule_mode": "daily",
    "schedule_time": "09:00",
    "schedule_date": "",
    "schedule_count": 1,
    "max_workers": 10,
    "schedule_devices": [],
}


def load_config() -> dict:
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {**DEFAULT_CONFIG, **data}
    except FileNotFoundError:
        return DEFAULT_CONFIG.copy()
    except Exception:
        return DEFAULT_CONFIG.copy()


def format_schedule_status(config: dict) -> str:
    if not config.get("enable_schedule"):
        return "定时巡检：已关闭"

    mode = config.get("schedule_mode", "daily")
    time_str = config.get("schedule_time", "09:00")
    workers = config.get("max_workers", 10)
    fmt = config.get("output_format", "HTML")
    count = len(config.get("schedule_devices") or [])
    rounds = _normalize_count(config)

    if mode == "date":
        date_str = config.get("schedule_date") or "未设置"
        return (
            f"定时巡检：已开启 | 模式=指定日期 | 日期={date_str} | 时间={time_str} | "
            f"次数={rounds} | 设备={count} 台 | 并发={workers} | 输出={fmt}"
        )
    return (
        f"定时巡检：已开启 | 模式=每日 | 时间={time_str} | "
        f"次数={rounds} | 设备={count} 台 | 并发={workers} | 输出={fmt}"
    )


def _normalize_count(config: dict) -> int:
    try:
        n = int(config.get("schedule_count") or 1)
    except (TypeError, ValueError):
        n = 1
    return max(1, min(n, 24))


class ScheduleManager:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._last_trigger_key: Optional[str] = None

    async def start(self):
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def reload_and_log(self):
        """设置变更后重新读取并输出日志"""
        config = load_config()
        manager.broadcast_sync("INFO", format_schedule_status(config))

    async def _loop(self):
        while True:
            try:
                self._check_and_run()
            except Exception as e:
                manager.broadcast_sync("ERROR", f"定时巡检检查异常: {e}")
            await asyncio.sleep(30)

    def _check_and_run(self):
        config = load_config()
        if not config.get("enable_schedule"):
            return

        schedule_time = config.get("schedule_time", "09:00")
        schedule_mode = config.get("schedule_mode", "daily")
        now = datetime.now()

        try:
            hour, minute = map(int, schedule_time.split(":"))
        except (ValueError, AttributeError):
            manager.broadcast_sync("ERROR", f"定时巡检配置无效：时间格式错误 ({schedule_time})")
            return

        if now.hour != hour or now.minute != minute:
            return

        if schedule_mode == "date":
            schedule_date = config.get("schedule_date") or ""
            if not schedule_date:
                return
            if now.strftime("%Y-%m-%d") != schedule_date:
                return
            trigger_key = f"date_{schedule_date}_{schedule_time}"
        else:
            trigger_key = f"daily_{now.strftime('%Y-%m-%d')}_{schedule_time}"

        if self._last_trigger_key == trigger_key:
            return

        self._last_trigger_key = trigger_key
        devices = config.get("schedule_devices") or []

        manager.broadcast_sync("INFO", f"定时巡检触发：{format_schedule_status(config)}")

        if schedule_mode == "date":
            manager.broadcast_sync("INFO", "指定日期任务已触发，将在本次执行后自动关闭定时")

        rounds = _normalize_count(config)
        workers = int(config.get("max_workers") or 10)
        output_format = config.get("output_format", "HTML")

        if rounds <= 1:
            launched = launch_inspection(
                devices=devices,
                max_workers=workers,
                output_format=output_format,
                source="schedule",
            )
            if launched and schedule_mode == "date":
                self._disable_after_date_run()
            return

        threading.Thread(
            target=self._run_multi_rounds,
            args=(devices, workers, output_format, rounds, schedule_mode),
            daemon=True,
        ).start()

    def _run_multi_rounds(self, devices, workers, output_format, rounds, schedule_mode):
        clear_stop_flag()
        for i in range(1, rounds + 1):
            if was_stop_requested():
                manager.broadcast_sync("WARNING", f"定时多轮巡检已中止（{i - 1}/{rounds}）")
                break

            if i > 1:
                while is_inspection_running():
                    if was_stop_requested():
                        manager.broadcast_sync("WARNING", f"定时多轮巡检已中止（{i - 1}/{rounds}）")
                        return
                    time.sleep(0.5)
                if was_stop_requested():
                    manager.broadcast_sync("WARNING", f"定时多轮巡检已中止（{i - 1}/{rounds}）")
                    break
                manager.broadcast_sync("INFO", f"定时巡检第 {i}/{rounds} 次开始")

            launched = launch_inspection(
                devices=devices,
                max_workers=workers,
                output_format=output_format,
                source="schedule",
            )
            if not launched:
                manager.broadcast_sync("WARNING", f"定时巡检第 {i}/{rounds} 次未能启动，后续轮次取消")
                break

        if schedule_mode == "date":
            self._disable_after_date_run()

    def _disable_after_date_run(self):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config["enable_schedule"] = False
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            manager.broadcast_sync("INFO", "指定日期巡检已触发，定时巡检已自动关闭")
        except Exception as e:
            manager.broadcast_sync("WARNING", f"自动关闭定时巡检失败: {e}")


schedule_manager = ScheduleManager()
