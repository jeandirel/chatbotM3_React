import datetime
import re
from typing import Optional


def _format_conversation_title(raw: str, fallback: str, max_len: int = 60) -> str:
    """Nettoie une question utilisateur pour en faire un titre court lisible."""
    if not raw:
        return fallback

    title = raw.strip()
    title = re.sub(r"[?!.]+$", "", title)
    patterns = [
        r"^comment\s+(faire\s+(pour\s+)?)?",
        r"^comment\s+se\s+",
        r"^comment\s+est[-\s]*ce\s+que\s+",
        r"^je\s+(veux|voudrais|souhaite)\s+",
    ]
    for pat in patterns:
        title = re.sub(pat, "", title, flags=re.IGNORECASE).strip()

    if title:
        title = title[:1].upper() + title[1:]

    if len(title) > max_len:
        title = title[: max_len - 1].rstrip() + "…"

    return title or fallback


def compute_session_title(messages: list, fallback: str) -> str:
    for msg in messages:
        if msg.get("role") == "user":
            content = (msg.get("content") or "").strip()
            if content:
                return _format_conversation_title(content, fallback)
    return fallback


def format_elapsed_time(dt: Optional[datetime.datetime]) -> str:
    """Retourne un libellé temps relatif (ex: 'Il y a 2h')."""
    if not dt:
        return ""
    now = datetime.datetime.now(datetime.timezone.utc)
    delta = now - dt
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "À l'instant"
    if minutes < 60:
        return f"Il y a {minutes} min"
    hours = minutes // 60
    if hours < 24:
        return f"Il y a {hours}h"
    days = hours // 24
    if days == 1:
        return "Hier"
    if days < 7:
        return f"Il y a {days} jours"
    weeks = days // 7
    return f"Il y a {weeks} sem"


def build_preview(messages: list, max_len: int = 72) -> str:
    """Construit un court aperçu à partir des messages de la session."""
    for msg in messages:
        txt = (msg.get("content") or "").strip()
        if not txt:
            continue
        preview = txt.replace("\n", " ")
        return (preview[: max_len - 1] + "…") if len(preview) > max_len else preview
    return "Aucun message pour l'instant."

