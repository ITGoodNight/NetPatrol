"""
项目路径常量（开发 / PyInstaller 打包通用）
"""
import os
import shutil
import sys

CONFIG_DIR_NAME = 'config'
REPORTS_DIR_NAME = 'reports'


def is_frozen() -> bool:
    return getattr(sys, 'frozen', False)


def get_app_root() -> str:
    """可写数据根目录：开发时为项目根，打包后为 exe 所在目录"""
    if is_frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def get_bundle_root() -> str:
    """只读资源根目录（前端 dist、默认配置模板等）"""
    if is_frozen():
        return getattr(sys, '_MEIPASS', get_app_root())
    return get_app_root()


APP_ROOT = get_app_root()
ROOT_DIR = APP_ROOT
BUNDLE_ROOT = get_bundle_root()

CONFIG_DIR = os.path.join(APP_ROOT, CONFIG_DIR_NAME)
REPORTS_DIR = os.path.join(APP_ROOT, REPORTS_DIR_NAME)
HISTORY_PATH = os.path.join(APP_ROOT, 'inspection_history.json')
APP_CONFIG_PATH = os.path.join(CONFIG_DIR, 'config.json')
COMMANDS_PATH = os.path.join(CONFIG_DIR, 'commands.txt')
FRONTEND_DIST = os.path.join(BUNDLE_ROOT, 'frontend', 'dist')
BUNDLE_CONFIG_DIR = os.path.join(BUNDLE_ROOT, CONFIG_DIR_NAME)


def ensure_config_dir() -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)


def ensure_runtime_dirs() -> None:
    """确保运行时可写目录存在，并在首次启动时复制内置默认配置"""
    ensure_config_dir()
    os.makedirs(REPORTS_DIR, exist_ok=True)

    if is_frozen():
        # 打包内可能以 config.json 或 config.example.json 的形式提供默认配置，两者都接受
        sources = {
            'config.json': ('config.json', 'config.example.json'),
            'commands.txt': ('commands.txt',),
        }
        for name, candidates in sources.items():
            dst = os.path.join(CONFIG_DIR, name)
            if os.path.exists(dst):
                continue
            for candidate in candidates:
                src = os.path.join(BUNDLE_CONFIG_DIR, candidate)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                    break


def migrate_legacy_config_files() -> None:
    """将根目录旧配置文件迁移到 config/ 目录（仅首次）"""
    ensure_config_dir()
    legacy_map = {
        os.path.join(APP_ROOT, 'config.json'): APP_CONFIG_PATH,
        os.path.join(APP_ROOT, 'commands.txt'): COMMANDS_PATH,
    }
    for legacy, target in legacy_map.items():
        if os.path.exists(legacy) and not os.path.exists(target):
            shutil.move(legacy, target)
