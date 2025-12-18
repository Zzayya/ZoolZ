"""Local logging and summarization for JEFF (no external APIs)."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

ROOT = Path(__file__).parent
LOG_DIR = ROOT / "data" / "logs"
SUMMARY_DIR = ROOT / "data" / "summaries"
LOG_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)


def _today_str() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _ts_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def log_interaction(
    user: str,
    message: str,
    reply: str,
    meta: Optional[Dict[str, Union[str, int]]] = None,
    log_date: Optional[str] = None,
) -> None:
    """
    Append a chat interaction to today's log (JSONL).
    """
    log_date = log_date or _today_str()
    log_path = LOG_DIR / f"{log_date}.jsonl"
    entry = {
        "ts": _ts_iso(),
        "user": user or "unknown",
        "message": message or "",
        "reply": reply or "",
        "meta": meta or {},
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_log(log_date: str) -> List[Dict[str, str]]:
    """
    Read a day's log into memory.
    """
    log_path = LOG_DIR / f"{log_date}.jsonl"
    if not log_path.exists():
        return []
    entries: List[Dict[str, str]] = []
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def summarize_day(log_date: Optional[str] = None) -> Dict[str, Union[str, int, List[str]]]:
    """
    Create a simple summary for a given day:
    - total interactions
    - unique users
    - first/last timestamps
    - sample of distinct questions
    """
    log_date = log_date or _today_str()
    entries = read_log(log_date)
    if not entries:
        summary = {
            "date": log_date,
            "total": 0,
            "users": [],
            "first_ts": None,
            "last_ts": None,
            "sample_questions": [],
        }
    else:
        users = list({e.get("user", "unknown") for e in entries})
        sample_questions = []
        seen = set()
        for e in entries:
            q = (e.get("message") or "").strip()
            if q and q not in seen:
                sample_questions.append(q)
                seen.add(q)
            if len(sample_questions) >= 5:
                break
        summary = {
            "date": log_date,
            "total": len(entries),
            "users": users,
            "first_ts": entries[0].get("ts"),
            "last_ts": entries[-1].get("ts"),
            "sample_questions": sample_questions,
        }

    summary_path = SUMMARY_DIR / f"{log_date}.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return summary


def list_summaries() -> List[Dict[str, Union[str, int, List[str]]]]:
    """
    Read all saved summaries in date order.
    """
    summaries: List[Dict[str, Union[str, int, List[str]]]] = []
    for path in sorted(SUMMARY_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            summaries.append(data)
        except json.JSONDecodeError:
            continue
    return summaries

