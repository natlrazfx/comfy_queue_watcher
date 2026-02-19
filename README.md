# ComfyUI Queue Watcher (Telegram)

Watches a running ComfyUI instance and sends a Telegram message when the queue
finishes (all running + pending jobs are done).

[![Watch the video](https://img.youtube.com/vi/4BUMfJ3zpeo/maxresdefault.jpg)](https://youtu.4BUMfJ3zpeo)

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
message. The script also logs to `../queue_watcher.log`.

## Run alongside ComfyUI (startup script snippet)

If you start ComfyUI from a script, add these lines before launching ComfyUI
to start the watcher as a background process. Adjust paths for your setup.

```bash
# Load .env if present (Telegram + optional COMFY_URL)
ENV_FILE="../.env"
if [ -f "$ENV_FILE" ]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

# Activate venv if you use one
COMFY_DIR="../ComfyUI"
VENV_DIR="../venv"
cd "$COMFY_DIR"
source "$VENV_DIR/bin/activate"

# Start Queue Watcher (stop previous instance first)
pkill -f "comfy_queue_watcher.py" >/dev/null 2>&1 || true
nohup python ../comfy_queue_watcher.py >> ../queue_watcher.log 2>&1 &
```

## Notes

- If the script logs `Telegram env missing`, verify `TELEGRAM_BOT_TOKEN` and
  `TELEGRAM_CHAT_ID`.
- If ComfyUI is not ready, the script will keep retrying until it is reachable.
- To verify your chat ID, message your bot and check `getUpdates` in the Bot API
  response (`https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`) or use a bot
  like @userinfobot to display your ID.

## How to get Telegram chat ID

- For personal chats: send a message to your bot, then use a bot like
  @userinfobot to get your user ID.
- For groups: add the bot to the group, send a message, and read updates via the
  Bot API (or use a helper bot) to get the group chat ID.

## Don@tes
**If any of this turns out to be useful for you - I’m glad.  
And if you feel like supporting it:  
☕ 1–2 coffees are more than enough ☺️**  

[Click to Buy me a Coffee](https://buymeacoffee.com/natlrazfx)
