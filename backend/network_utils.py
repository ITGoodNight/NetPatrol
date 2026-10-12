"""
网络测试工具：Ping / Tracert
"""
import asyncio
import platform
import re
from typing import AsyncIterator, Optional, Tuple

PING_TIME_RE = re.compile(r'(?:time[=<](\d+)|时间[=<](\d+)ms?)', re.I)
TARGET_RE = re.compile(r'^[a-zA-Z0-9.\-_]{1,253}$')

IS_WINDOWS = platform.system().lower() == 'windows'


def validate_target(target: str) -> str:
    target = (target or '').strip()
    if not target or not TARGET_RE.match(target):
        raise ValueError('无效的目标地址，仅支持 IP 或域名')
    return target


def _decode_output(data: bytes) -> str:
    if IS_WINDOWS:
        return data.decode('gbk', errors='replace')
    return data.decode('utf-8', errors='replace')


async def ping_once(target: str, timeout_ms: int = 3000) -> Tuple[Optional[float], str, str]:
    """
    执行一次 Ping，返回 (延迟毫秒, 状态, 原始输出片段)
    状态: ok | timeout | failed
    """
    if IS_WINDOWS:
        cmd = ['ping', '-n', '1', '-w', str(timeout_ms), target]
    else:
        timeout_sec = max(1, timeout_ms // 1000)
        cmd = ['ping', '-c', '1', '-W', str(timeout_sec), target]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    text = _decode_output(stdout or b'')

    lower = text.lower()
    if 'timed out' in lower or '请求超时' in text or '100% 丢失' in text or '100% loss' in lower:
        return None, 'timeout', text.strip()
    if proc.returncode != 0 and 'ttl=' not in lower and 'TTL=' not in text:
        return None, 'failed', text.strip()

    match = PING_TIME_RE.search(text)
    if match:
        latency = float(match.group(1) or match.group(2))
        return latency, 'ok', text.strip()

    if proc.returncode == 0:
        return None, 'ok', text.strip()
    return None, 'failed', text.strip()


async def stream_tracert(target: str, max_hops: int = 30) -> AsyncIterator[str]:
    """逐行输出 tracert / traceroute 结果"""
    max_hops = max(1, min(int(max_hops), 64))
    if IS_WINDOWS:
        cmd = ['tracert', '-d', '-h', str(max_hops), target]
    else:
        cmd = ['traceroute', '-n', '-m', str(max_hops), target]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    if not proc.stdout:
        await proc.wait()
        return

    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        decoded = _decode_output(line).rstrip('\r\n')
        if decoded:
            yield decoded

    await proc.wait()
