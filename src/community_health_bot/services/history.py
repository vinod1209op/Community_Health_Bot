import csv
from datetime import date
from pathlib import Path
from typing import Iterable, List, Optional

from ..core.models import HistoryEntry


def read_history(path: Path) -> List[HistoryEntry]:
    if not path.exists():
        return []
    entries: List[HistoryEntry] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                try:
                    run_date = row.get("date")
                    subreddit = row.get("subreddit")
                    if not run_date or not subreddit:
                        continue
                    entries.append(
                        HistoryEntry(
                            date=run_date,
                            subreddit=subreddit,
                            total_posts=int(row.get("total_posts", 0)),
                            unanswered=int(row.get("unanswered", 0)),
                            unanswered_rate=float(row.get("unanswered_rate", 0.0)),
                            median_ttf_minutes=_parse_optional_float(row.get("median_ttf_minutes")),
                        )
                    )
                except Exception:
                    continue
    except Exception:
        return []
    return entries


def append_history(path: Path, entries: Iterable[HistoryEntry]) -> None:
    entries = list(entries)
    if not entries:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["date", "subreddit", "total_posts", "unanswered", "unanswered_rate", "median_ttf_minutes"]
    write_header = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "date": entry.date,
                    "subreddit": entry.subreddit,
                    "total_posts": entry.total_posts,
                    "unanswered": entry.unanswered,
                    "unanswered_rate": entry.unanswered_rate,
                    "median_ttf_minutes": entry.median_ttf_minutes
                    if entry.median_ttf_minutes is not None
                    else "",
                }
            )


def recent_history_for_subreddit(entries: List[HistoryEntry], subreddit: str, limit: int = 6) -> List[HistoryEntry]:
    filtered = [entry for entry in entries if entry.subreddit == subreddit]
    # Sort descending by date string (ISO format).
    filtered.sort(key=lambda e: e.date, reverse=True)
    return filtered[:limit]


def _parse_optional_float(value) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None
