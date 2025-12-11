Scheduling examples (cron)
--------------------------

Run report hourly:
```
0 * * * * /usr/bin/env bash -lc 'cd /path/to/repo && source .venv/bin/activate && PYTHONPATH=src python3 -m cli --subreddits r/example1 r/example2 --mode report --config config.example.yaml >> logs/bot.log 2>&1'
```

Run weekly post on Mondays 9am:
```
0 9 * * MON /usr/bin/env bash -lc 'cd /path/to/repo && source .venv/bin/activate && PYTHONPATH=src python3 -m cli --subreddits r/example1 r/example2 --mode post --post-to r/example1 --config config.example.yaml >> logs/bot.log 2>&1'
```

Notes:
- Keep polling low (hourly is plenty) to stay within Reddit’s limits.
- Rotate logs and purge output files older than 48h (built-in purge handles summaries).
