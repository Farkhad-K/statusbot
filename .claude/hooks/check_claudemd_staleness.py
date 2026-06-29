#!/usr/bin/env python3
"""
PreToolUse hook on Bash — fires before every git commit.
Blocks the commit with exit 2 if tracked source files are staged
but CLAUDE.md was not updated in the same staging area.

This forces Claude to run /update-claude-md and re-stage CLAUDE.md
before the commit is allowed to proceed.
"""
import sys
import json
import subprocess

data = json.load(sys.stdin)
cmd = data.get("command", "")

# Only inspect git commit commands — pass everything else through.
if "git commit" not in cmd:
    sys.exit(0)


def staged_files(paths: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--"] + paths,
        capture_output=True,
        text=True,
    )
    return [f for f in result.stdout.strip().splitlines() if f]


SOURCE_FILES = ["bot.py", "keyboards.py", "db.py", "config.py", "plan.md"]

source_staged = staged_files(SOURCE_FILES)
claudemd_staged = staged_files(["CLAUDE.md"])

if source_staged and not claudemd_staged:
    changed = ", ".join(source_staged)
    print("⚠  CLAUDE.md is stale — source files were changed but CLAUDE.md was not updated.")
    print(f"   Staged source files: {changed}")
    print()
    print("   Fix: run /update-claude-md, then `git add CLAUDE.md`, then retry the commit.")
    sys.exit(2)
