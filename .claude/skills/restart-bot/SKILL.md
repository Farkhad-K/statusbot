---
name: restart-bot
description: Restart the statusbot systemd service and show the last 20 log lines to confirm it started cleanly.
disable-model-invocation: true
---

Run this exact command and show the full output to the user without commentary:

```sh
sudo systemctl restart statusbot && sleep 2 && journalctl -u statusbot -n 20 --no-pager
```

If `systemctl` is not found or the service does not exist, say:
"statusbot systemd service not found — run `python bot.py` manually to start the bot."
