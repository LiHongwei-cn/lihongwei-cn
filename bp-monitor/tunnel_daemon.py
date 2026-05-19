"""SSH tunnel daemon — keeps localhost.run alive and updates miniprogram config."""
import subprocess
import time
import re
import sys
import urllib.request
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


def start_tunnel():
    """Start tunnel, return (process, url). Blocks until URL is ready."""
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


def check_health(url: str) -> bool:
    try:
        req = urllib.request.Request(url + "/api/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def kill_proc(proc) -> None:
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def main() -> None:
    print("[daemon] starting tunnel watchdog...")
    proc, url = None, None
    fail_count = 0

    while True:
        if proc is None or proc.poll() is not None:
            if proc:
                print("[daemon] ssh process exited, restarting...")
            proc, url = start_tunnel()
            if url:
                update_app_js(url)
                fail_count = 0
            else:
                fail_count += 1
                wait = min(fail_count * 5, 30)
                print(f"[daemon] failed to get tunnel URL, retry in {wait}s...")
                time.sleep(wait)
                continue

        # Active health check
        if url and not check_health(url):
            fail_count += 1
            print(f"[daemon] health check failed ({fail_count}), restarting tunnel...")
            kill_proc(proc)
            proc = None
            url = None
            time.sleep(3)
            continue

        fail_count = 0
        time.sleep(15)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[daemon] stopped")
        sys.exit(0)
