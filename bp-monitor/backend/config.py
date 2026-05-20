import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


def get_env(key: str) -> str:
    val = os.environ.get(key)
    if val:
        return val
    raise KeyError(f"{key} 未设置，请在 backend/.env 文件中配置")


DEV_MODE = os.environ.get("BP_DEV_MODE", "").lower() in ("1", "true", "yes")

DEEPSEEK_API_KEY = get_env("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-pro"

if DEV_MODE:
    WECHAT_APPID = os.environ.get("WECHAT_APPID", "")
    WECHAT_SECRET = os.environ.get("WECHAT_SECRET", "")
else:
    WECHAT_APPID = get_env("WECHAT_APPID")
    WECHAT_SECRET = get_env("WECHAT_SECRET")

CRON_SECRET_TOKEN = get_env("CRON_SECRET_TOKEN")

DB_PATH = Path(__file__).parent / "bp_monitor.db"
