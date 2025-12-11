from collections import Counter
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import List, Optional

import praw

from ..core.models import MetricsSnapshot, PostSummary, SubredditReport, Trend, UnansweredSummary


def _detect_post_type(post: praw.models.Submission) -> str:
    if getattr(post, "poll_data", None):
        return "poll"
    if getattr(post, "is_gallery", False):
        return "gallery"
    if getattr(post, "is_video", False):
        return "video"
    if post.is_self:
        return "self"
    return "link"


def _time_to_first_comment_minutes(post: praw.models.Submission) -> Optional[float]:
    """
    Return minutes from post creation to first comment, if any.
    This is limited to avoid heavy API use; call only for a small subset.
    """
    try:
        post.comments.replace_more(limit=0)
    except Exception:
        return None
    comments = list(post.comments)
    if not comments:
        return None
    first_comment = min(comments, key=lambda c: getattr(c, "created_utc", post.created_utc))
    delta_seconds = float(first_comment.created_utc - post.created_utc)
    return max(delta_seconds, 0) / 60.0


def _looks_like_question(title: str) -> bool:
    lowered = title.lower()
    interrogatives = ("who", "what", "when", "where", "why", "how", "does", "is", "are", "can", "should")
    return "?" in title or lowered.startswith(interrogatives)


def collect_weekly_report(
    reddit: praw.Reddit,
    subreddit_name: str,
    top_posts_limit: int = 10,
    unanswered_limit: int = 10,
    include_sections: Optional[dict] = None,
) -> SubredditReport:
    subreddit = reddit.subreddit(subreddit_name)
    now = datetime.now(timezone.utc)
    one_week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    top_posts: List[PostSummary] = []
    unanswered_posts: List[UnansweredSummary] = []
    rising_posts: List[PostSummary] = []
    aging_unanswered: List[UnansweredSummary] = []

    # Metrics containers
    post_type_mix: Counter[str] = Counter()
    flair_distribution: Counter[str] = Counter()
    time_to_first_comment_samples: List[float] = []
    total_posts_week = 0
    unanswered_week = 0
    total_posts_prev = 0
    unanswered_prev = 0

    # Top posts (current week)
    for post in subreddit.top(time_filter="week", limit=top_posts_limit):
        top_posts.append(
            PostSummary(
                title=post.title,
                score=post.score,
                comments=post.num_comments,
                permalink=f"https://reddit.com{post.permalink}",
            )
        )

    # Recent posts for metrics and unanswered detection
    recent_limit = max(max(top_posts_limit, unanswered_limit) * 5, 50)
    ttf_cap = 30  # limit time-to-first-comment sampling to avoid excessive API calls
    ttf_checked = 0

    for post in subreddit.new(limit=recent_limit):
        created = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
        flair = post.link_flair_text or "None"
        if created >= one_week_ago:
            total_posts_week += 1
            flair_distribution[flair] += 1
            post_type_mix[_detect_post_type(post)] += 1
            hours_old = (now - created).total_seconds() / 3600.0
            if post.num_comments == 0 and len(unanswered_posts) < unanswered_limit:
                unanswered_week += 1
                question_like = _looks_like_question(post.title)
                unanswered_summary = UnansweredSummary(
                    title=post.title,
                    permalink=f"https://reddit.com{post.permalink}",
                    question_like=question_like,
                )
                unanswered_posts.append(unanswered_summary)
                if 48 <= hours_old <= 120 and len(aging_unanswered) < unanswered_limit:
                    aging_unanswered.append(unanswered_summary)
            elif ttf_checked < ttf_cap:
                ttf = _time_to_first_comment_minutes(post)
                if ttf is not None:
                    time_to_first_comment_samples.append(ttf)
                ttf_checked += 1

            # rising posts: simple heuristic of score velocity for fresh posts (<48h)
            if hours_old <= 48 and hours_old > 0:
                score_velocity = post.score / hours_old
                if score_velocity >= 5 and len(rising_posts) < top_posts_limit:
                    rising_posts.append(
                        PostSummary(
                            title=post.title,
                            score=post.score,
                            comments=post.num_comments,
                            permalink=f"https://reddit.com{post.permalink}",
                        )
                    )
        elif two_weeks_ago <= created < one_week_ago:
            total_posts_prev += 1
            if post.num_comments == 0:
                unanswered_prev += 1

    unanswered_rate = (unanswered_week / total_posts_week) if total_posts_week else 0.0
    median_ttf = median(time_to_first_comment_samples) if time_to_first_comment_samples else None

    metrics = MetricsSnapshot(
        total_posts=total_posts_week,
        unanswered=unanswered_week,
        unanswered_rate=unanswered_rate,
        median_time_to_first_comment_minutes=median_ttf,
        post_type_mix=dict(post_type_mix),
        flair_distribution=dict(flair_distribution),
    )

    trends: List[Trend] = []
    if total_posts_prev:
        delta_posts = total_posts_week - total_posts_prev
        trends.append(
            Trend(
                metric="posts_week_over_week",
                current=float(total_posts_week),
                previous=float(total_posts_prev),
                delta=float(delta_posts),
            )
        )
    if total_posts_prev:
        prev_unanswered_rate = unanswered_prev / total_posts_prev if total_posts_prev else 0.0
        delta_unanswered_rate = unanswered_rate - prev_unanswered_rate
        trends.append(
            Trend(
                metric="unanswered_rate_week_over_week",
                current=unanswered_rate,
                previous=prev_unanswered_rate,
                delta=delta_unanswered_rate,
            )
        )

    report = SubredditReport(
        top_posts=top_posts,
        rising_posts=rising_posts,
        unanswered=unanswered_posts,
        aging_unanswered=aging_unanswered,
        metrics=metrics,
        trends=trends,
        include_sections=include_sections
        or {
            "stats": True,
            "trends": True,
            "top_posts": True,
            "unanswered": True,
        },
    )
    return report
