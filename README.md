Community Health Bot (Reddit)
=============================

Purpose
-------
- Read-only analytics helper for a small, fixed set of subreddits (example: `r/example1`, `r/example2`) to support moderators/community managers.
- Generates weekly summaries (top posts, engagement stats, unanswered questions) and optionally posts the summary once per week with moderator approval.
- No DMs, no voting/karma actions, no cross-posting or spam. Scope is limited to the listed subreddits.
- Endpoints/actions: read-only (`/r/{sub}/top`, `/r/{sub}/new`) + optional weekly post. Frequency: hourly reads (configurable), weekly post max 1x/week.

Project layout
--------------
```
src/
  community_health_bot/
    __init__.py
    cli.py                    # CLI entrypoint
    config/
      __init__.py
      settings.py             # Settings and env validation
    core/
      __init__.py
      models.py               # Shared dataclasses for summaries and metrics
    reddit/
      __init__.py
      client.py               # PRAW client factory
    services/
      __init__.py
      analytics.py            # Fetch subreddit data and compute weekly reports
      reporting.py            # Markdown generation and file output
      publisher.py            # Optional Reddit submission helper
      webhook.py              # Optional Slack/Discord webhook delivery
      cache.py                # Purge old summary files
      history.py              # Metrics history storage/lookup
      logging.py              # Structured logging helpers
```

Why not Devvit?
---------------
- Needs server-side scheduled aggregation across multiple subreddits with external alerting/exports.
- Current Devvit flow does not cover scheduled cross-subreddit aggregation plus optional weekly post outside their execution environment.
 - External delivery (webhooks) and cron-style scheduling are outside Devvit scope.

Data handling and compliance
----------------------------
- Only fetches public posts/comments.
- No storage beyond transient processing; optional local cache purged every run. Recommend deleting any logs/caches within 48 hours.
- Honors user deletions: do not persist IDs/content from deleted posts/comments or deleted users.
- No selling/sharing/training/ads; non-commercial use only.
- Uses descriptive User-Agent: `server:community-health-bot:1.0.0 (by /u/YourBotAccount)`.
- Respects rate limits and headers (`X-Ratelimit-*`); default polling is low-frequency (hourly reads, weekly post).

Form-ready answers (adapt to your details)
------------------------------------------
- Benefit/purpose: Improve moderation efficiency and member experience by summarizing weekly activity, surfacing unanswered questions, and highlighting top posts for the specified subreddits. Reduces moderator workload and improves response times.
- Detailed description: Read-only fetch of posts/comments from `r/<your list>` 1-4 times per hour to compute engagement metrics; once per week optionally posts a summary thread if moderators approve. No DMs, no voting, no cross-subreddit posting. Data retained transiently and cleared within 48 hours.
- What is missing from Devvit: Need scheduled, cross-subreddit aggregation and optional external alerting/logging not supported in Devvit today.
- Link to source/platform: this repo (include GitHub link when published).
- Subreddits: list the exact subreddits; include proof of mod permission if you are not a moderator.
- Username operating the bot: the dedicated bot account you will run (not your main).

Local setup
-----------
1) Python 3.9+ recommended.
2) `python -m venv .venv && source .venv/bin/activate`
3) `pip install -r requirements.txt` (or `pip install .[dev]` from the repo root)
4) Fill in `.env` with your Reddit script creds (client id/secret, bot username/password, descriptive user agent).
5) Run: `PYTHONPATH=src python3 -m community_health_bot.cli --subreddits r/techsupport r/linuxquestions r/HomeNetworking r/sysadmin r/InformationTechnology r/Office365 --mode report --config config.yaml`
6) Optional: install as a CLI via `pipx install .` (or `pip install .`), then run `community-health-bot --help`

Configuration
-------------
Environment variables (see `.env`):
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`: Script-type app credentials.
- `REDDIT_USERNAME`, `REDDIT_PASSWORD`: Bot account for script auth.
- `USER_AGENT`: Descriptive UA string.
- `OUTPUT_DIR`: Where to write summary files (optional).
- `WEBHOOK_URL`: Optional Slack/Discord webhook for sending summaries.
- YAML (optional): `config.yaml` shows per-subreddit overrides:
  - `top_posts_limit`, `unanswered_limit`
  - `include_sections`: toggle `stats`, `trends`, `top_posts`, `unanswered`

Usage
-----
- Report-only (no posting):
  `PYTHONPATH=src python3 -m community_health_bot.cli --subreddits r/techsupport r/linuxquestions r/HomeNetworking r/sysadmin r/InformationTechnology r/Office365 --mode report --config config.yaml`
- Post weekly summary (requires `submit` scope and mod approval):
  `PYTHONPATH=src python3 -m community_health_bot.cli --subreddits r/techsupport r/linuxquestions r/HomeNetworking r/sysadmin r/InformationTechnology r/Office365 --mode post --post-to r/techsupport --config config.yaml`
- The CLI backs off automatically when `X-Ratelimit-Remaining` is low, using `X-Ratelimit-Reset` plus a small buffer.

What it does
------------
- Fetches top posts from the past week, recent new posts, and computes weekly metrics.
- Adds unanswered triage (questions tagged) plus an aging-unanswered bucket (48-120h) to help prioritize responses.
- Keeps a lightweight metrics history (`output/metrics_history.csv`) to show recent run stats in the report.
- Metrics: unanswered count/rate, median time-to-first-comment (sampled), post type mix, flair distribution, week-over-week trends, rising posts (score velocity).
- Produces a Markdown summary locally (stdout and optional file); sends to webhook if configured.
- In `post` mode, submits the summary to the specified subreddit once per run.

Docker
------
Build/run locally:
```
docker build -t community-health-bot .
docker run --rm -v $(pwd)/.env:/app/.env community-health-bot --help
```

Notes
-----
- Keep polling modest (e.g., hourly via cron) to stay within 100 QPM and be courteous.
- Do not expand scope beyond declared subreddits without updating your application and documentation.
- If any post/comment/user is deleted, purge related stored data immediately.
- Output cleanup: summaries older than 48h are auto-purged after each run.
- See `README_CRON_EXAMPLE.md` for cron snippets and `README_SAFETY_CHECKLIST.md` for compliance steps.
