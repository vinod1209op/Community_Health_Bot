from pathlib import Path

from community_health_bot.core.models import (
    HistoryEntry,
    MetricsSnapshot,
    PostSummary,
    SubredditReport,
    Trend,
    UnansweredSummary,
)
from community_health_bot.services.reporting import build_markdown


def test_build_markdown_basic():
    reports = {
        "r/example": SubredditReport(
            top_posts=[PostSummary(title="t", score=10, comments=5, permalink="https://x")],
            rising_posts=[],
            unanswered=[UnansweredSummary(title="q", permalink="https://y")],
            aging_unanswered=[UnansweredSummary(title="old q", permalink="https://z", question_like=True)],
            metrics=MetricsSnapshot(
                total_posts=1,
                unanswered=1,
                unanswered_rate=1.0,
                median_time_to_first_comment_minutes=5.0,
                post_type_mix={"self": 1},
                flair_distribution={"None": 1},
            ),
            trends=[
                Trend(metric="posts_week_over_week", current=1, previous=2, delta=-1),
                Trend(metric="unanswered_rate_week_over_week", current=1.0, previous=0.5, delta=0.5),
            ],
            history=[
                HistoryEntry(
                    date="2024-01-01",
                    subreddit="r/example",
                    total_posts=1,
                    unanswered=1,
                    unanswered_rate=1.0,
                    median_ttf_minutes=5.0,
                )
            ],
        )
    }
    md = build_markdown(["r/example"], reports)
    assert "Weekly Community Health Summary" in md
    assert "Posts this week: 1" in md
    assert "Unanswered rate" in md
    assert "Top posts this week" in md
    assert "Unanswered recent posts" in md
    assert "Aging unanswered" in md
    assert "(question)" in md
    assert "Recent history" in md
