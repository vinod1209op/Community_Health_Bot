from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PostSummary:
    title: str
    score: int
    comments: int
    permalink: str


@dataclass
class UnansweredSummary:
    title: str
    permalink: str
    question_like: bool = False


@dataclass
class MetricsSnapshot:
    total_posts: int
    unanswered: int
    unanswered_rate: float
    median_time_to_first_comment_minutes: Optional[float]
    post_type_mix: Dict[str, int]
    flair_distribution: Dict[str, int]


@dataclass
class Trend:
    metric: str
    current: float
    previous: float
    delta: float


@dataclass
class SubredditReport:
    top_posts: List[PostSummary]
    rising_posts: List[PostSummary]
    unanswered: List[UnansweredSummary]
    metrics: MetricsSnapshot
    trends: List[Trend]
    aging_unanswered: List[UnansweredSummary] = field(default_factory=list)
    history: List["HistoryEntry"] = field(default_factory=list)


# Convenience factory for empty counters when needed.
def empty_counter() -> Counter:
    return Counter()


@dataclass
class HistoryEntry:
    date: str  # ISO date string (YYYY-MM-DD)
    subreddit: str
    total_posts: int
    unanswered: int
    unanswered_rate: float
    median_ttf_minutes: Optional[float]
