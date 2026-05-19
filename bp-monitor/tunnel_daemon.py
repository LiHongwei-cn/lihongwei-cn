"""SSH tunnel daemon — keeps localhost.run alive and updates miniprogram config."""
import subprocess
import time
import re
import sys
from pathlib import Path

APP_JS = Path(__file__).parent / "miniprogram" / "app.js"
TUNNEL_CMD = [
    "ssh", "-o", "StrictHostKeyChecking=no",
    "-o", "ServerAliveInterval=30",
    "-o", "ServerAliveCountMax=3",
    "-o", "ExitOnForwardFailure=yes",
    "-R", "80:localhost:8080",
    "nokey@localhost.run"
]

URL_PATTERN = re.compile(r"https://[a-z0-9]+\.lhr\.life")


def update_app_js(url: str) -> None:
    content = APP_JS.read_text(encoding="utf-8")
    new_content = URL_PATTERN.sub(url, content)
    if new_content != content:
        APP_JS.write_text(new_content, encoding="utf-8")
        print(f"[daemon] app.js updated → {url}")


def run_tunnel() -> str:
    """Start tunnel, return URL when ready."""
    proc = subprocess.Popen(
        TUNNEL_CMD,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    url = None
    for line in proc.stdout:
        line = line.strip()
        print(f"[tunnel] {line}")
        m = URL_PATTERN.search(line)
        if m and "tunneled with tls" in line:
            url = m.group(0)
            break
    return proc, url


def main() -> None:
    print("[daemon] starting tunnel watchdog...")
    proc, url = None, None

    while True:
        if proc is None or proc.poll() is not None:
            if proc:
                print("[daemon] tunnel died, restarting...")
            else:
                print("[daemon] starting tunnel...")
            proc, url = run_tunnel()
            if url:
                update_app_js(url)
            else:
                print("[daemon] failed to get tunnel URL, retrying in 10s...")
                time.sleep(10)
                continue

        time.sleep(15)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[daemon] stopped")
        sys.exit(0)
