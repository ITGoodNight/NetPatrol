"""
巡检执行历史记录
"""
import json
from datetime import datetime
from typing import List, Dict, Any

from backend.paths import HISTORY_PATH

MAX_RECORDS = 30


def _load() -> List[Dict[str, Any]]:
    try:
        with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except FileNotFoundError:
        return []
    except Exception:
        return []


def _save(records: List[Dict[str, Any]]) -> None:
    with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def list_history() -> List[Dict[str, Any]]:
    return _load()


def append_history(
    source: str,
    total: int,
    successful: int,
    failed: int,
    retry_rounds: int = 0,
    retry_recovered: int = 0,
) -> Dict[str, Any]:
    now = datetime.now()
    record = {
        "id": now.strftime("%Y%m%d_%H%M%S"),
        "time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "source": source,
        "source_label": "定时任务" if source == "schedule" else "手动任务",
        "total": total,
        "successful": successful,
        "failed": failed,
        "retry_rounds": retry_rounds,
        "retry_recovered": retry_recovered,
    }
    records = _load()
    records.insert(0, record)
    _save(records[:MAX_RECORDS])
    return record


def clear_history() -> int:
    records = _load()
    count = len(records)
    _save([])
    return count
