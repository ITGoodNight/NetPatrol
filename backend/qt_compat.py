"""
PySide6 Qt 核心类的轻量兼容 Shim
当 PySide6 未安装时（Web 后端模式），提供等价的纯 Python 实现，
使 modules/inspector.py 无需修改即可在 FastAPI 环境中运行。
"""

try:
    # 如果 PySide6 已安装，直接使用原生类
    from PySide6.QtCore import Signal, QObject  # noqa: F401
except ImportError:
    # ── 纯 Python 替代实现 ──────────────────────────────────────────────────
    class _SignalImpl:
        """模拟 Qt Signal 实例，支持 connect/emit"""

        def __init__(self, *args):
            self._slots = []

        def connect(self, slot):
            if slot not in self._slots:
                self._slots.append(slot)

        def disconnect(self, slot=None):
            if slot is None:
                self._slots.clear()
            elif slot in self._slots:
                self._slots.remove(slot)

        def emit(self, *args):
            for slot in list(self._slots):
                try:
                    slot(*args)
                except Exception:
                    pass

    class _SignalDescriptor:
        """描述符：让 Signal 在类体中声明时正确绑定到实例"""

        def __init__(self, *args):
            self._args = args
            self._name = None

        def __set_name__(self, owner, name):
            self._name = name

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self
            attr = f"_signal_{self._name}"
            if not hasattr(obj, attr):
                setattr(obj, attr, _SignalImpl(*self._args))
            return getattr(obj, attr)

    Signal = _SignalDescriptor

    class QObject:
        """模拟 Qt QObject 基类"""

        def __init__(self, *args, **kwargs):
            pass
