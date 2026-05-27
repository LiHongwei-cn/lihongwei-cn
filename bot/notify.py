"""发送 Telegram 通知。用法: python notify.py <消息文本>"""
import sys
from pathlib import Path

from telegram import Bot

from config import get_env

TOKEN = get_env("TELEGRAM_TOKEN")
CHAT_ID_FILE = Path(__file__).parent / "chat_id.txt"


def send_telegram(text: str, retries: int = 2):
    if not CHAT_ID_FILE.exists():
        print("chat_id 文件不存在，跳过通知")
        return False

    chat_id = CHAT_ID_FILE.read_text().strip()
    if not chat_id:
        print("chat_id 为空，跳过通知")
        return False

    bot = Bot(token=TOKEN)
    for attempt in range(retries + 1):
        try:
            bot.send_message(chat_id=int(chat_id), text=text)
            print("通知已发送")
            return True
        except Exception as e:
            if attempt < retries:
                print(f"发送失败，重试 ({attempt + 1}/{retries}): {e}")
            else:
                print(f"通知发送失败: {e}")
                return False
    return False


if __name__ == "__main__":
    args = sys.argv[1:]
    msg = " ".join(args) if args else ""
    if msg:
        send_telegram(msg)
    else:
        print("用法: python notify.py <消息文本>")
