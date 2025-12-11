from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..core.models import HistoryEntry, MetricsSnapshot, PostSummary, SubredditReport, Trend, UnansweredSummary


def generate_mock_report(
    subreddit_name: str,
    top_posts_limit: int = 5,
    unanswered_limit: int = 5,
    include_sections: Optional[Dict[str, bool]] = None,
) -> SubredditReport:
    now = datetime.utcnow().date()
    top_posts: List[PostSummary] = [
        PostSummary(
            title=f"[Mock] Helpful thread #{i} in {subreddit_name}",
            score=150 - i * 10,
            comments=40 - i * 5,
            permalink=f"https://reddit.com/r/{subreddit_name}/mock_top_{i}",
        )
        for i in range(1, top_posts_limit + 1)
    ]
    rising_posts: List[PostSummary] = [
        PostSummary(
            title=f"[Mock] Rising post #{i} in {subreddit_name}",
            score=60 + i * 5,
            comments=8 + i * 3,
            permalink=f"https://reddit.com/r/{subreddit_name}/mock_rising_{i}",
        )
        for i in range(1, min(4, top_posts_limit) + 1)
    ]
    unanswered: List[UnansweredSummary] = [
        UnansweredSummary(
            title=f"[Mock] Unanswered question #{i} in {subreddit_name}?",
            permalink=f"https://reddit.com/r/{subreddit_name}/mock_unanswered_{i}",
            question_like=True,
        )
        for i in range(1, unanswered_limit + 1)
    ]
    aging_unanswered = unanswered[: max(1, min(3, unanswered_limit))]

    metrics = MetricsSnapshot(
        total_posts=42,
        unanswered=len(unanswered),
        unanswered_rate=len(unanswered) / 42,
        median_time_to_first_comment_minutes=12.5,
        post_type_mix={"self": 30, "link": 8, "video": 4},
        flair_distribution={"Solved": 10, "Unresolved": 5, "None": 27},
    )
    trends = [
        Trend(metric="posts_week_over_week", current=42, previous=38, delta=4),
        Trend(metric="unanswered_rate_week_over_week", current=metrics.unanswered_rate, previous=0.2, delta=0.0),
    ]
    history = [
        HistoryEntry(
            date=(now - timedelta(days=7 * i)).isoformat(),
            subreddit=subreddit_name,
            total_posts=40 + i,
            unanswered=5 + i,
            unanswered_rate=0.12 + i * 0.01,
            median_ttf_minutes=15 - i,
        )
        for i in range(3)
    ]

    return SubredditReport(
        top_posts=top_posts,
        rising_posts=rising_posts,
        unanswered=unanswered,
        aging_unanswered=aging_unanswered,
        metrics=metrics,
        trends=trends,
        history=history,
        include_sections=include_sections
        or {"stats": True, "trends": True, "top_posts": True, "unanswered": True},
    )
