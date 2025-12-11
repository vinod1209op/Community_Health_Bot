import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .config.settings import SubredditConfig, load_settings, validate_user_agent
from .core.models import HistoryEntry, SubredditReport
from .reddit.client import create_reddit_client
from .services.analytics import collect_weekly_report
from .services.cache import purge_older_than
from .services.history import append_history, read_history, recent_history_for_subreddit
from .services.logging import log_json, log_rate_limit, setup_logger
from .services.rate_limit import maybe_backoff_if_low
from .services.publisher import submit_summary
from .services.reporting import build_markdown, write_output
from .services.webhook import send_webhook
from .services.mock_data import generate_mock_report


from . import __version__


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Community health bot.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--env-file",
        type=str,
        help="Path to .env file (defaults to .env in the current directory)",
    )
    parser.add_argument(
        "--subreddits",
        nargs="+",
        required=True,
        help="List of subreddits to summarize (e.g., r/example1 r/example2)",
    )
    parser.add_argument(
        "--mode",
        choices=["report", "post"],
        default="report",
        help="report: print/write summary; post: also submit weekly summary",
    )
    parser.add_argument(
        "--post-to",
        help="Subreddit to post the summary to (required for post mode)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of top posts to consider per subreddit (overridden by YAML config if provided)",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to YAML config for per-subreddit settings",
    )
    parser.add_argument(
        "--mock-data",
        action="store_true",
        help="Generate mock data instead of calling Reddit (good for testing output)",
    )
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    config_path = Path(args.config).expanduser() if args.config else None
    env_path = Path(args.env_file).expanduser() if args.env_file else None
    settings = load_settings(env_file=env_path, config_file=config_path, allow_missing=args.mock_data)
    if not args.mock_data:
        validate_user_agent(settings.user_agent)
    logger = setup_logger()
    run_date = datetime.now().date().isoformat()
    history_path = settings.output_dir / "metrics_history.csv"
    existing_history = read_history(history_path)
    new_history_entries: List[HistoryEntry] = []

    if args.mode == "post" and not args.post_to:
        raise SystemExit("--post-to is required in post mode")
    if args.mock_data and args.mode == "post":
        raise SystemExit("--mock-data can only be used in report mode")

    reddit = None if args.mock_data else create_reddit_client(settings)
    reports: Dict[str, SubredditReport] = {}

    for name in args.subreddits:
        sub_cfg: SubredditConfig = settings.subreddit_configs.get(
            name, SubredditConfig(name=name, top_posts_limit=args.limit)
        )
        if args.mock_data:
            report = generate_mock_report(
                name,
                top_posts_limit=sub_cfg.top_posts_limit,
                unanswered_limit=sub_cfg.unanswered_limit,
                include_sections=sub_cfg.include_sections,
            )
        else:
            report = collect_weekly_report(
                reddit,
                name,
                top_posts_limit=sub_cfg.top_posts_limit,
                unanswered_limit=sub_cfg.unanswered_limit,
                include_sections=sub_cfg.include_sections,
            )
        report.history = recent_history_for_subreddit(existing_history, name)
        reports[name] = report
        new_history_entries.append(
            HistoryEntry(
                date=run_date,
                subreddit=name,
                total_posts=report.metrics.total_posts,
                unanswered=report.metrics.unanswered,
                unanswered_rate=report.metrics.unanswered_rate,
                median_ttf_minutes=report.metrics.median_time_to_first_comment_minutes,
            )
        )
        if reddit:
            maybe_backoff_if_low(reddit, logger)

    append_history(history_path, new_history_entries)

    markdown = build_markdown(args.subreddits, reports)
    print(markdown)
    out_path = write_output(settings.output_dir, markdown)
    print(f"\nSaved summary to {out_path}")
    log_json(logger, "generated_summary", output=str(out_path), subreddits=args.subreddits)
    removed = purge_older_than(settings.output_dir, days=2)
    if removed:
        log_json(logger, "purged_old_summaries", removed=removed)

    if args.mode == "post":
        title = f"Weekly community summary - {datetime.now().date()}"
        permalink = submit_summary(reddit, args.post_to, title, markdown)
        print(f"Posted summary to {permalink}")
        log_json(logger, "posted_summary", permalink=permalink, subreddit=args.post_to)

    if reddit:
        log_rate_limit(logger, reddit)
    send_webhook(settings.webhook_url, "Community Health Summary", markdown[:1500])


if __name__ == "__main__":
    run()
