#!/usr/bin/env python3
"""
PostToolUse hook — runs py_compile on any .py file after it is edited or written.
Exit 1 is a soft warning: Claude sees the message but the edit is already saved.
"""
import sys
import json
import subprocess

data = json.load(sys.stdin)
fp = data.get("file_path", "")

if not fp.endswith(".py"):
    sys.exit(0)

result = subprocess.run(
    ["python3", "-m", "py_compile", fp],
    capture_output=True,
    text=True,
)
if result.returncode != 0:
    print(f"✗ Syntax error in {fp}:")
    print(result.stderr.strip())
    sys.exit(1)

print(f"✓ {fp} — syntax OK")
