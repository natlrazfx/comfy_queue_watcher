# ComfyUI Queue Watcher (Telegram)

Watches a running ComfyUI instance and sends a Telegram message when the queue
finishes (all running + pending jobs are done).

## Requirements

- Python 3.9+
- `requests` (`pip install requests`)
- A Telegram bot token and a chat ID
- Network access to the ComfyUI server and Telegram API

## Setup

Set the environment variables (examples below). You can set them in your shell
or in a `.env` file and load it yourself before running the script.

```powershell
$env:COMFY_URL="http://127.0.0.1:8188"
$env:TELEGRAM_BOT_TOKEN="123456:abcdef..."
$env:TELEGRAM_CHAT_ID="123456789"
$env:WATCHER_POLL_SECONDS="2.0"
```

### Environment variables

- `COMFY_URL` (optional): Base URL for ComfyUI. Default: `http://127.0.0.1:8188`
- `TELEGRAM_BOT_TOKEN` (required): Bot token from @BotFather
- `TELEGRAM_CHAT_ID` (required): Target chat ID (user, group, or channel)
- `WATCHER_POLL_SECONDS` (optional): Poll interval in seconds. Default: `2.0`

## Run

```powershell
python .\comfy_queue_watcher.py
```

When the queue transitions from busy to empty, you will receive a Telegram
message. The script also logs to `/workspace/queue_watcher.log`.

## Run with ComfyUI (startup script example)

If you already start ComfyUI from a startup script, you can launch the watcher
in the same script. Adjust paths to your environment. Example (bash):

```bash
#!/bin/bash
set -e

echo "[INFO] Starting run_gpu.sh"

# =========================
# Paths
# =========================
COMFY_DIR="/workspace/ComfyUI"
VENV_DIR="/workspace/venv"
ENV_FILE="/workspace/.env"

OLLAMA_ROOT="/workspace/ollama"
OLLAMA_BIN="$OLLAMA_ROOT/bin/ollama"
OLLAMA_MODELS="$OLLAMA_ROOT/models"
OLLAMA_LOG="$OLLAMA_ROOT/ollama.log"

export OLLAMA_HOST="http://127.0.0.1:11434"
export OLLAMA_MODELS="$OLLAMA_MODELS"

# =========================
# Load .env (Telegram + optional COMFY_URL etc.)
# =========================
if [ -f "$ENV_FILE" ]; then
  set -a
  source "$ENV_FILE"
  set +a
  echo "[INFO] .env loaded: token=${TELEGRAM_BOT_TOKEN:+SET} chat=${TELEGRAM_CHAT_ID:+SET}"
else
  echo "[WARN] $ENV_FILE not found (Telegram notifications will not work)"
fi

# =========================
# Activate venv
# =========================
cd "$COMFY_DIR"
source "$VENV_DIR/bin/activate"

# =========================
# Start Queue Watcher
# =========================
# Stop previous watcher if any (optional but useful)
pkill -f "comfy_queue_watcher.py" >/dev/null 2>&1 || true

nohup python /workspace/comfy_queue_watcher.py >> /workspace/queue_watcher.log 2>&1 &
echo "[INFO] Queue watcher started (log: /workspace/queue_watcher.log)"

# =========================
# Ollama setup
# =========================
mkdir -p "$OLLAMA_ROOT/bin" "$OLLAMA_MODELS"

if [ ! -x "$OLLAMA_BIN" ]; then
  echo "[INFO] Ollama binary not found in storage."

  if command -v ollama >/dev/null 2>&1; then
    echo "[INFO] System Ollama found, copying to storage..."
    cp "$(which ollama)" "$OLLAMA_BIN"
    chmod +x "$OLLAMA_BIN"
  else
    echo "[INFO] Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "[INFO] Copying Ollama binary to storage..."
    cp "$(which ollama)" "$OLLAMA_BIN"
    chmod +x "$OLLAMA_BIN"
  fi
fi

if ! pgrep -f "ollama serve" >/dev/null 2>&1; then
  echo "[INFO] Starting Ollama server..."
  nohup "$OLLAMA_BIN" serve > "$OLLAMA_LOG" 2>&1 &
fi

echo "[INFO] Waiting for Ollama API..."
for i in {1..30}; do
  if curl -fsS "$OLLAMA_HOST/api/tags" >/dev/null 2>&1; then
    echo "[INFO] Ollama is up."
    break
  fi
  sleep 1
done

if ! "$OLLAMA_BIN" list | grep -q "qwen2.5vl:7b"; then
  echo "[INFO] Pulling model qwen2.5vl:7b..."
  "$OLLAMA_BIN" pull qwen2.5vl:7b
fi

# =========================
# Start ComfyUI
# =========================
echo "[INFO] Starting ComfyUI..."
exec python main.py \
  --enable-manager \
  --preview-method auto \
  --use-sage-attention \
  --listen 0.0.0.0 \
  --port 8188
```

## Notes

- If the script logs `Telegram env missing`, verify `TELEGRAM_BOT_TOKEN` and
  `TELEGRAM_CHAT_ID`.
- If ComfyUI is not ready, the script will keep retrying until it is reachable.

## How to get Telegram chat ID

- For personal chats: send a message to your bot, then use a bot like
  @userinfobot to get your user ID.
- For groups: add the bot to the group, send a message, and read updates via the
  Bot API (or use a helper bot) to get the group chat ID.
