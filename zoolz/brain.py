"""
ZoolZ Brain - lightweight local responses (no external AI).
Extended to log interactions to JEFF for summaries.
"""

from typing import Dict, List, Optional
from jeff.logger import log_interaction


def generate_zoolz_reply(message: str, status_fetcher=None, user: Optional[str] = None) -> Dict[str, str]:
    """
    Generate a lightweight, offline-friendly reply and log it.

    Args:
        message: User prompt.
        status_fetcher: Optional callable returning process status dict.
        user: Optional username for logging.
    """
    text = (message or "").strip()
    lower = text.lower()
    reply_parts: List[str] = []

    if not text:
        reply = "Hit me with anything about ZoolZ, modeling, or server status."
        log_interaction(user or "unknown", message or "", reply, {"topic": "general"})
        return {"reply": reply}

    if any(k in lower for k in ['status', 'health', 'running', 'process']):
        if status_fetcher:
            status = status_fetcher()
            active = status.get('active_programs', [])
            running = list(status.get('running_processes', {}).keys())
            reply_parts.append(f"Active programs: {active or ['none']}")
            reply_parts.append(f"Running helpers: {running or ['none']}")
        else:
            reply_parts.append("Status fetcher not available.")

    if any(k in lower for k in ['model', 'stl', 'cookie', 'mesh', 'cutter']):
        reply_parts.append("Modeling tips: keep meshes <10M verts, repair/simplify before booleans, high-contrast PNGs for cookie cutters.")

    if 'parametric' in lower or 'scad' in lower:
        reply_parts.append("Parametric CAD: create shapes → combine → export STL. Reset registry if memory grows.")

    if 'people' in lower or 'footprint' in lower:
        reply_parts.append("People/Digital tools run sync by default; use SSE endpoints for progress.")

    if 'opencv' in lower:
        reply_parts.append("OpenCV: installer auto-picks a Catalina-friendly wheel; rerun setup if cv2 ever fails.")

    if 'redis' in lower or 'celery' in lower or 'background' in lower:
        reply_parts.append("Background tasks: start Redis + Celery for heavy Modeling jobs; otherwise routes run inline.")

    if 'public' in lower or 'network' in lower:
        reply_parts.append("Public access: bind 0.0.0.0:5001 and forward external 5001 → your Mac IP. Use scripts/network_check.sh.")

    if 'ai' in lower or 'brain' in lower or 'chat' in lower or 'jeff' in lower:
        reply_parts.append("JEFF is local-only right now. Summaries are stored daily under jeff/data/summaries.")

    if not reply_parts:
        reply_parts.append("Noted. Ask about modeling, setup, background tasks, or network and I'll share specifics.")

    reply_text = " ".join(reply_parts)
    log_interaction(user or "unknown", message, reply_text, {"topic": "chat"})
    return {"reply": reply_text}
