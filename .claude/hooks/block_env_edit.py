#!/usr/bin/env python3
"""
PreToolUse hook — blocks direct edits to .env (but allows .env.example).
Exit 2 cancels the tool call and shows the message to Claude.
"""
import sys
import json

data = json.load(sys.stdin)
fp = data.get("file_path", "")

if ".env" in fp and not fp.endswith(".env.example"):
    print(
        "⛔ Direct .env edits are blocked.\n"
        "   Edit .env.example instead (for template changes), or modify .env\n"
        "   manually in a terminal outside this session (for local secrets)."
    )
    sys.exit(2)
