from datetime import datetime, timedelta
from typing import Optional, Tuple

from utils.utils import dprint


def format_time_ago(date_str: str) -> str:
    dprint(f"format_time_ago(): date_str = {date_str}")

    if not date_str or not date_str.strip():
        return "neznámé datum"

    try:
        upload_time = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        dprint(f"format_time_ago(): ValueError: {e}")
        return "neznámé datum"
    except Exception as e:
        dprint(f"format_time_ago(): Neočekávaná chyba: {e}")
        return "neznámé datum"

    # Teprve teď je upload_time platný
    now = datetime.now()
    delta = now - upload_time
    total_seconds = int(delta.total_seconds())

    if total_seconds < 60:
        return "právě teď"
    elif total_seconds < 3600:
        mins = total_seconds // 60
        return f"před {mins} minut{'ou' if mins == 1 else 'ami'}"
    elif total_seconds < 3 * 86400:
        hours = total_seconds // 3600
        return f"před {hours} hodin{'ou' if hours == 1 else 'ami'}"
    else:
        days = total_seconds // 86400
        return f"před {days} {'dnem' if days == 1 else 'dny'}"


def format_eta(seconds: Optional[float]) -> str:
    if seconds is None or seconds <= 0 or seconds == float('inf'):
        return "--:--:--"

    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_eta_and_finish(seconds: Optional[float]) -> Tuple[str, str]:
    """
    Vrátí:
        eta_str   → "00:02:13" nebo "--:--:--"
        finish_at → "18:45"   nebo "--:--"
    """
    if seconds is None or seconds <= 0 or seconds == float('inf'):
        return "--:--:--", "--:--"

    # ETA (zůstává stejné)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    eta_str = f"{h:02d}:{m:02d}:{s:02d}"

    # Čas dokončení = teď + ETA
    finish_time = datetime.now() + timedelta(seconds=int(seconds))
    finish_str = finish_time.strftime("%H:%M")

    return eta_str, finish_str
