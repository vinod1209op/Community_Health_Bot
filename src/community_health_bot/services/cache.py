import shutil
from datetime import datetime, timedelta
from pathlib import Path


def purge_older_than(directory: Path, days: int = 2) -> int:
    if not directory.exists():
        return 0
    cutoff = datetime.now() - timedelta(days=days)
    removed = 0
    for path in directory.iterdir():
        if not path.is_file():
            continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        if mtime < cutoff:
            try:
                path.unlink()
                removed += 1
            except Exception:
                continue
    return removed
