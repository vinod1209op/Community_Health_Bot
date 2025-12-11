import time
import os
from pathlib import Path

from community_health_bot.services.cache import purge_older_than


def test_purge_older_than(tmp_path: Path):
    old_file = tmp_path / "old.txt"
    new_file = tmp_path / "new.txt"
    old_file.write_text("old")
    new_file.write_text("new")
    # set mtime for old file to 3 days ago
    three_days_ago = time.time() - 3 * 24 * 3600
    os.utime(old_file, (three_days_ago, three_days_ago))

    removed = purge_older_than(tmp_path, days=2)
    assert removed == 1
    assert not old_file.exists()
    assert new_file.exists()
