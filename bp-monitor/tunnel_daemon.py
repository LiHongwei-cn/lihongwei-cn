"""SSH tunnel daemon — keeps localhost.run alive and updates miniprogram config."""
import subprocess
import time
import re
import sys
import os
import signal
import urllib.request
from pathlib import Path

APP_JS = Path(__file__).parent / "miniprogram" / "app.js"

IS_WINDOWS = sys.platform == "win32"

TUNNEL_CMD = [
    "ssh", "-o", "StrictHostKeyChecking=no",
    "-o", "ServerAliveInterval=30",
    "-o", "ServerAliveCountMax=3",
    "-o", "ExitOnForwardFailure=yes",
    "-R", "80:localhost:8080",
    "nokey@localhost.run"
]

URL_PATTERN = re.compile(r"https://[a-z0-9]+\.lhr\.life")

RETRY_BASE = 5
MAX_RETRY = 60
HEALTH_INTERVAL = 30


def kill_existing_ssh():
    """Kill all existing SSH processes to avoid zombie accumulation."""
    try:
        if IS_WINDOWS:
            subprocess.run(
                ["taskkill", "/F", "/IM", "ssh.exe"],
                capture_output=True, timeout=10
            )
        else:
            subprocess.run(
                ["pkill", "-f", "ssh.*localhost.run"],
                capture_output=True, timeout=5
            )
    except Exception:
        pass
    time.sleep(1)


def update_app_js(url: str) -> None:
    content = APP_JS.read_text(encoding="utf-8")
    new_content = URL_PATTERN.sub(url, content)
    if new_content != content:
        APP_JS.write_text(new_content, encoding="utf-8")
        print(f"[daemon] app.js updated -> {url}")


def start_tunnel():
    """Start tunnel, return (process, url). Blocks until URL is ready."""
    proc = subprocess.Popen(
        TUNNEL_CMD,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        creationflags=subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0,
    )
    url = None
    timeout = 60
    start = time.time()
    for line in proc.stdout:
        line = line.strip()
        print(f"[tunnel] {line}")
        m = URL_PATTERN.search(line)
        if m and "tunneled with tls" in line:
            url = m.group(0)
            break
        if time.time() - start > timeout:
            print("[daemon] tunnel startup timed out after 60s")
            break
    return proc, url


def check_health(url: str) -> bool:
    try:
        req = urllib.request.Request(url + "/api/health", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


def kill_proc(proc) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        if IS_WINDOWS:
            proc.terminate()
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
            proc.wait(timeout=3)
        except Exception:
            pass


def main() -> None:
    print("[daemon] starting tunnel watchdog...")
    kill_existing_ssh()

    proc, url = None, None
    fail_count = 0

    while True:
        if proc is None or proc.poll() is not None:
            if proc:
                print("[daemon] ssh process exited, restarting...")
                kill_existing_ssh()
            proc, url = start_tunnel()
            if url:
                update_app_js(url)
                fail_count = 0
            else:
                fail_count += 1
                wait = min(fail_count * RETRY_BASE, MAX_RETRY)
                print(f"[daemon] failed to get tunnel URL, retry in {wait}s...")
                time.sleep(wait)
                continue

        if url and not check_health(url):
            fail_count += 1
            print(f"[daemon] health check failed ({fail_count}), restarting tunnel...")
            kill_proc(proc)
            proc = None
            url = None
            time.sleep(3)
            continue

        fail_count = 0
        time.sleep(HEALTH_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[daemon] stopped")
        sys.exit(0)
