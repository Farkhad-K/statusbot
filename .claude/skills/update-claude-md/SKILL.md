---
name: update-claude-md
description: Refresh CLAUDE.md to reflect the current state of the codebase. Run before committing when bot.py, keyboards.py, db.py, config.py, or plan.md changed.
---

Read these files: `bot.py`, `keyboards.py`, `db.py`, `config.py`, `.env.example`, `plan.md`.

Overwrite `CLAUDE.md` with exactly the sections listed below and nothing else.
After writing, run `wc -l CLAUDE.md` — if the result is over 80 lines, trim until it is.

---

## What to include (in this order)

### 1. Title
`# StatusBot — CLAUDE.md`

### 2. ## What This Is
1-3 sentences. Cover: what the bot does, what DB operations it performs, and that it has no web layer. Read bot.py to confirm the current description is accurate.

### 3. ## File Map
Markdown table — File | Purpose. One row per `.py` file. One-line purpose each. Do not list venv, __pycache__, or config templates.

### 4. ## Services & DB Operations
Markdown table — Key | Field changed | Target value | Table config var. Derive rows from `config.py` and `db.py`. One row per service (q1, q2, k, and any others present in Config).

### 5. ## FSM States
An ASCII diagram in a `text` code fence. Show states by name and the transitions between them. Include any Back/Cancel paths that exist. Max 10 lines total inside the fence.

### 6. ## Auth
One line: what `ALLOWED_IDS` does, where it lives, what empty means.

### 7. ## Running
A `sh` code fence with the exact command to start the bot. Read README.md or CLAUDE.md history to confirm it hasn't changed.

### 8. ## Key Constraints
Bullet list. Max 6 bullets. Each max 1 line. Only include constraints that:
- Are non-obvious (a developer new to the codebase would not guess them)
- Would silently break or corrupt the bot if violated
- Are not already expressed by the code itself

---

## What NOT to include

- Git history, PR summaries, recent changes, changelogs
- Setup instructions, installation steps, prereqs (that is README.md)
- Explanations of Python, asyncpg, or python-telegram-bot
- Future plans, TODOs, roadmap (that is plan.md)
- Comments about why code was written a certain way
- Anything that a developer could learn in 30 seconds by reading the source file

---

## Quality check before saving

Ask yourself: "If a Claude agent or a new developer read only this file, would they know
what not to break, what files to touch for each concern, and how to run the bot?"
If yes, save it. If not, add only what answers those questions.
