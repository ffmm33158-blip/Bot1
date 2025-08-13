# Telegram Notes Organizer Bot

Bot in Arabic for organizing personal notes with categories, priorities, reminders, and interactive inline keyboards.

## Features
- 8 commands: /start, /add, /notes, /edit, /search, /stats, /backup, /menu
- JSON storage with auto-backup
- Reminder scheduler (APScheduler)
- Inline keyboards, pagination
- Flask web server: /health, /status
- Works with polling or webhook (Render compatible)

## Requirements
- Python 3.10+
- Environment variables:
  - `TELEGRAM_BOT_TOKEN` (required)
  - `MODE` = `polling` or `webhook` (default: polling)
  - `WEBHOOK_URL` (required if MODE=webhook)
  - `PORT` (default: 8080)

## Local Run (Polling)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=YOUR_TOKEN
python -m app.main
```

## Webhook Run (Render)
- Set env vars TELEGRAM_BOT_TOKEN, MODE=webhook, WEBHOOK_URL=https://your-service.onrender.com/telegram/webhook
- Render will bind PORT (default 10000-). The app listens on `0.0.0.0:$PORT`.

## Data
- JSON store at `data/notes.json`
- Auto-backups at `data/backups/notes_auto_YYYYMMDD_HHMMSS.json`

## Health
- `GET /health` -> {"status":"ok"}
- `GET /status` -> summary JSON
