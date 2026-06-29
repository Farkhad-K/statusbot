# StatusBot

A Telegram bot that updates record statuses in PostgreSQL databases. Supports three services: **Q1** (Questionary v1), **Q2** (Questionary v2), and **K2** (Collaboration v2).

---

## Prerequisites

- Python 3.11 or newer
- PostgreSQL databases accessible via connection strings
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your Telegram user ID (get it from [@userinfobot](https://t.me/userinfobot))

---

## Quick Start

Run all commands from inside the project directory.

### 1. Clone the repository

```sh
git clone <repo-url>
cd statusbot
```

### 2. Create a virtual environment

```sh
python3 -m venv .venv
```

### 3. Activate and install dependencies

```sh
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure environment

```sh
cp .env.example .env
```

Open `.env` and fill in your real values (see [Configuration](#configuration) below).

### 5. Run manually (to verify it works)

```sh
source .venv/bin/activate
python bot.py
```

Send `/start` to your bot in Telegram. The **"So'rovnoma/Shartnoma tasdiqlash"** button
should appear in the keyboard area. If it does, everything is wired up correctly.
Stop with `Ctrl+C`.

---

## Configuration

All settings live in `.env` (never commit this file — it is git-ignored).

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Telegram bot token from @BotFather |
| `ALLOWED_IDS` | Comma-separated Telegram user IDs allowed to use the bot |
| `Q1_DSN` | PostgreSQL DSN for the Q1 database |
| `Q1_TABLE` | Table name for Q1 records |
| `Q2_DSN` | PostgreSQL DSN for the Q2 database |
| `Q2_TABLE` | Table name for Q2 records |
| `K_DSN` | PostgreSQL DSN for the K2 (collaboration) database |
| `K_TABLE` | Table name for K2 records (typically `contracts`) |

**DSN format:**

```
postgresql://user:password@host:5432/dbname
```

---

## Bot Workflow

```
/start
└─ "Salom!" + [So'rovnoma/Shartnoma tasdiqlash]   ← persistent keyboard button
        │
        ▼ (tap button)
   Service menu
   ├─ Q1 · Questionary v1  →  send ID  [⬅][✖]  →  sets status = "confirmed"
   ├─ Q2 · Questionary v2  →  send ID  [⬅][✖]
   │           └─ [✅ Approve → 6 Approve For Contract]  [⬅][✖]
   │              [🔢 Choose status]
   │                   └─ 3 Elma Success             [⬅ back to action][✖]
   │                      5 Pending Expert Approve
   │                      6 Approve For Contract
   │                      7 Cancelled
   └─ K2 · Collaboration v2  →  send ID  [⬅][✖]  →  sets status_id = 8
```

**Navigation:**
- **⬅ Orqaga** — go back one step (or return to service menu).
- **✖ Bekor qilish** — cancel the entire flow; the keyboard button remains visible.

Only one bot message is visible at a time — each step deletes the previous bot message
before sending the next one.

---

## Running as a systemd Service (Ubuntu)

This registers the bot as a background service that starts automatically on boot and restarts itself on failure.

> **Run every command below from inside the project directory.**

### 1. Create the service file

This command is generic — it reads your current username and project path automatically:

```sh
sudo tee /etc/systemd/system/statusbot.service > /dev/null << EOF
[Unit]
Description=StatusBot — Telegram status updater
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
EnvironmentFile=$PWD/.env
ExecStart=$PWD/.venv/bin/python bot.py
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

### 2. Enable and start

```sh
sudo systemctl daemon-reload
sudo systemctl enable statusbot
sudo systemctl start statusbot
```

### 3. Verify it is running

```sh
sudo systemctl status statusbot
```

---

## Service Management

| Action | Command |
|---|---|
| Start | `sudo systemctl start statusbot` |
| Stop | `sudo systemctl stop statusbot` |
| Restart | `sudo systemctl restart statusbot` |
| Disable autostart | `sudo systemctl disable statusbot` |
| View live logs | `journalctl -u statusbot -f` |
| View last 100 lines | `journalctl -u statusbot -n 100` |

---

## Updating the Bot

```sh
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart statusbot
```

## Removing the Service

```sh
sudo systemctl stop statusbot
sudo systemctl disable statusbot
sudo rm /etc/systemd/system/statusbot.service
sudo systemctl daemon-reload
```
