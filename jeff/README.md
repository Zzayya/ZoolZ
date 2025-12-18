# JEFF - Local Chat Logging

Purpose: keep a local record of chatbot interactions and daily summaries without any external AI calls.

Folders:
- `jeff/data/logs/` — daily JSONL logs (one line per interaction)
- `jeff/data/summaries/` — daily summaries (JSON)

Core code:
- `jeff/logger.py` — append interactions (`log_interaction`), read a day’s log, and write simple daily summaries (`summarize_day`, `list_summaries`).
- `zoolz/brain.py` — uses `log_interaction` when generating the local reply.
- `app.py` — `/api/zoolz/chat` now tags the user and logs to JEFF.

How to summarize a day (manual):
```bash
python3 - <<'PY'
from jeff.logger import summarize_day, list_summaries
print(summarize_day())  # defaults to today
print(list_summaries()[-3:])  # last few summaries
PY
```

No external APIs are used. Keys/configs for future models should live in `.env` (not implemented here).
