import os
import time
import requests
from datetime import datetime

COMFY_URL = os.getenv("COMFY_URL", "http://127.0.0.1:8188")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

LOG_PATH = "/workspace/queue_watcher.log"
POLL_SECONDS = float(os.getenv("WATCHER_POLL_SECONDS", "2.0"))

def log(msg: str):
    line = f"{datetime.now().isoformat(timespec='seconds')} | {msg}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()

def tg_send(text: str):
    if not BOT_TOKEN or not CHAT_ID:
        log("Telegram env missing: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is empty.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": text}, timeout=15)
        ok = (r.status_code == 200 and r.json().get("ok") is True)
        if not ok:
            log(f"Telegram send failed: status={r.status_code} resp={r.text[:300]}")
        return ok
    except Exception as e:
        log(f"Telegram exception: {e}")
        return False

def get_queue_sizes():
    # ComfyUI: /queue returns running & pending
    url = f"{COMFY_URL}/queue"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()

    # Robust parsing: different builds may name keys slightly differently.
    running = data.get("queue_running") or data.get("running") or []
    pending = data.get("queue_pending") or data.get("pending") or []

    # Sometimes they can be dict-like; normalize to counts
    def count(x):
        if x is None:
            return 0
        if isinstance(x, list):
            return len(x)
        if isinstance(x, dict):
            return len(x)
        return 0

    return count(running), count(pending)

def wait_for_comfy():
    log(f"Watcher starting. COMFY_URL={COMFY_URL}")
    while True:
        try:
            # /system_stats exists in many builds, but /queue is enough
            get_queue_sizes()
            log("ComfyUI is reachable.")
            return
        except Exception as e:
            log(f"Waiting for ComfyUI... ({e})")
            time.sleep(2)

def main():
    wait_for_comfy()

    last_total = 0
    saw_work = False

    # Small hello (optional)
    tg_send("ComfyUI watcher is online. I will notify when the queue finishes.")

    while True:
        try:
            running, pending = get_queue_sizes()
            total = running + pending

            if total > 0:
                saw_work = True

            # Trigger: was busy (or had queue) -> now empty
            if saw_work and last_total > 0 and total == 0:
                tg_send("Queue is empty. All jobs are finished.")
                log("Notified: queue became empty.")
                saw_work = False  # reset for next render

            last_total = total
            time.sleep(POLL_SECONDS)

        except Exception as e:
            log(f"Loop error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
