import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


DEV_MODE = os.environ.get("BP_DEV_MODE", "").lower() in ("1", "true", "yes")


def get_env(key: str, required: bool = True) -> str:
    val = os.environ.get(key)
    if val:
        return val
    if required:
        raise KeyError(f"{key} 未设置，请在 backend/.env 文件中配置")
    return ""


DEEPSEEK_API_KEY = get_env("DEEPSEEK_API_KEY", required=not DEV_MODE)
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-pro"

WECHAT_APPID = get_env("WECHAT_APPID", required=not DEV_MODE)
WECHAT_SECRET = get_env("WECHAT_SECRET", required=not DEV_MODE)

CRON_SECRET_TOKEN = get_env("CRON_SECRET_TOKEN", required=not DEV_MODE)

DB_PATH = Path(__file__).parent / "bp_monitor.db"
