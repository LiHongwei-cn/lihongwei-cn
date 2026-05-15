import os
import sys
import ssl
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError

def _get_env(key: str) -> str:
    val = os.environ.get(key)
    if val:
        return val
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as reg:
            val, _ = winreg.QueryValueEx(reg, key)
        os.environ[key] = val
        return val
    except Exception:
        raise KeyError(f"{key} 未设置")

TOKEN = _get_env("TELEGRAM_TOKEN")
CHAT_ID_FILE = Path(__file__).parent / "chat_id.txt"

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def send_telegram(text: str):
    if not CHAT_ID_FILE.exists():
        print("chat_id 文件不存在，跳过通知")
        return

    chat_id = CHAT_ID_FILE.read_text().strip()
    data = urlencode({"chat_id": chat_id, "text": text}).encode()
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        req = Request(url, data=data)
        urlopen(req, timeout=10, context=CTX)
        print("通知已发送")
    except URLError as e:
        print(f"通知发送失败: {e}")


if __name__ == "__main__":
    args = sys.argv[1:]
    carsim = False
    if "--carsim" in args:
        carsim = True
        args.remove("--carsim")

    msg = " ".join(args) if args else ""
    if carsim:
        steps_file = Path(__file__).parent / "carsim_steps.txt"
        if steps_file.exists():
            msg += "\n\n" + steps_file.read_text(encoding="utf-8")
    if msg:
        send_telegram(msg)
    else:
        print("用法: python notify.py [--carsim] <消息文本>")
