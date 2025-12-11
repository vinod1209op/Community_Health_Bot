import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import streamlit as st

# Ensure package is importable when running via `streamlit run ...` without install.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from community_health_bot.config.settings import SubredditConfig, load_settings, validate_user_agent
from community_health_bot.core.models import HistoryEntry, SubredditReport
from community_health_bot.reddit.client import create_reddit_client
from community_health_bot.services.analytics import collect_weekly_report
from community_health_bot.services.history import append_history, read_history, recent_history_for_subreddit
from community_health_bot.services.reporting import build_markdown


@st.cache_data(show_spinner=False)
def load_history(path: Path) -> List[HistoryEntry]:
    return read_history(path)


def main() -> None:
    st.set_page_config(page_title="Community Health Bot", layout="wide")
    st.title("Community Health Bot")
    st.caption("Reddit community health summaries (read-only analytics)")

    env_path = st.text_input("Environment file path", value=str(Path(".env").resolve()))
    config_path = st.text_input("YAML config path", value=str(Path("config.yaml").resolve()))

    if not Path(env_path).exists():
        st.warning("Env file not found; ensure credentials are set before running.")
    if not Path(config_path).exists():
        st.warning("Config file not found; using defaults from CLI args if provided.")

    subreddits_input = st.text_input(
        "Subreddits (space-separated, e.g., r/techsupport r/linuxquestions)", value="r/techsupport r/linuxquestions"
    )
    mode = st.radio("Mode", options=["report", "post"], index=0, horizontal=True)
    post_to = st.text_input("Post to subreddit (required for post mode)", value="")
    top_limit = st.slider("Top posts limit (default if not in YAML)", min_value=5, max_value=20, value=10)
    use_mock = st.checkbox("Use mock data (no Reddit calls)", value=False)

    if st.button("Generate summary"):
        run_summary(
            env_file=Path(env_path),
            config_file=Path(config_path) if config_path else None,
            subreddit_names=[s for s in subreddits_input.split() if s],
            mode=mode,
            post_to=post_to or None,
            default_top_limit=top_limit,
            use_mock=use_mock,
        )


def run_summary(
    env_file: Path,
    config_file: Path,
    subreddit_names: List[str],
    mode: str,
    post_to: str,
    default_top_limit: int,
    use_mock: bool = False,
) -> None:
    if mode == "post" and not post_to:
        st.error("Post mode requires a target subreddit.")
        return
    if use_mock and mode == "post":
        st.error("Mock data is only available in report mode.")
        return

    config_to_use = config_file if config_file and config_file.exists() else None
    if config_file and not config_file.exists():
        st.warning(f"Config file not found at {config_file}; falling back to CLI defaults.")

    if not use_mock:
        os.environ["DOTENV_PATH"] = str(env_file)
    settings = load_settings(env_file=env_file, config_file=config_to_use, allow_missing=use_mock)
    if not use_mock:
        validate_user_agent(settings.user_agent)

    history_path = settings.output_dir / "metrics_history.csv"
    history_entries = load_history(history_path)
    reddit = None if use_mock else create_reddit_client(settings)

    reports = {}
    new_history = []
    with st.spinner("Fetching subreddit data..."):
        for name in subreddit_names:
            sub_cfg: SubredditConfig = settings.subreddit_configs.get(
                name, SubredditConfig(name=name, top_posts_limit=default_top_limit)
            )
            if use_mock:
                from community_health_bot.services.mock_data import generate_mock_report

                report: SubredditReport = generate_mock_report(
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
            report.history = recent_history_for_subreddit(history_entries, name)
            reports[name] = report
            new_history.append(
                HistoryEntry(
                    date=datetime.utcnow().date().isoformat(),
                    subreddit=name,
                    total_posts=report.metrics.total_posts,
                    unanswered=report.metrics.unanswered,
                    unanswered_rate=report.metrics.unanswered_rate,
                    median_ttf_minutes=report.metrics.median_time_to_first_comment_minutes,
                )
            )

    append_history(history_path, new_history)
    markdown = build_markdown(subreddit_names, reports)
    st.success("Summary generated")
    st.code(markdown, language="markdown")

    if mode == "post":
        st.info("Posting via CLI mode is recommended. This UI is report-focused.")


if __name__ == "__main__":
    main()
