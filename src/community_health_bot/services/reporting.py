from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from ..core.models import HistoryEntry, SubredditReport, Trend, UnansweredSummary


def _fmt_percentage(value: float) -> str:
    return f"{value * 100:.1f}%"


def _fmt_minutes(value: float) -> str:
    return f"{value:.1f} min"


def _fmt_top_items(items: Dict[str, int], top_n: int = 5) -> str:
    if not items:
        return "n/a"
    sorted_items: List[Tuple[str, int]] = sorted(items.items(), key=lambda kv: kv[1], reverse=True)
    trimmed = sorted_items[:top_n]
    return ", ".join(f"{name} ({count})" for name, count in trimmed)


def _format_trends(trends: List[Trend]) -> List[str]:
    if not trends:
        return ["- No prior-week data"]
    lines: List[str] = []
    for trend in trends:
        if trend.metric == "posts_week_over_week":
            direction = "↑" if trend.delta > 0 else ("↓" if trend.delta < 0 else "→")
            lines.append(
                f"- Posts WoW: {trend.current:.0f} vs {trend.previous:.0f} ({direction} {trend.delta:+.0f})"
            )
        elif trend.metric == "unanswered_rate_week_over_week":
            direction = "↑" if trend.delta > 0 else ("↓" if trend.delta < 0 else "→")
            lines.append(
                f"- Unanswered rate WoW: {_fmt_percentage(trend.current)} vs {_fmt_percentage(trend.previous)} ({direction} {trend.delta:+.1%})"
            )
        else:
            lines.append(f"- {trend.metric}: {trend.current} (prev {trend.previous}, delta {trend.delta:+})")
    return lines


def _format_unanswered(unanswered: List[UnansweredSummary]) -> List[str]:
    lines: List[str] = []
    if not unanswered:
        return ["- None found"]
    for post in unanswered:
        label = " (question)" if getattr(post, "question_like", False) else ""
        lines.append(f"- [{post.title}]({post.permalink}){label}")
    return lines


def _format_history(history: List[HistoryEntry]) -> List[str]:
    if not history:
        return ["- No history yet (will populate after runs)"]
    lines: List[str] = []
    recent = history[:4]
    for entry in recent:
        lines.append(
            f"- {entry.date}: posts {entry.total_posts}, unanswered rate {_fmt_percentage(entry.unanswered_rate)}"
        )
    if len(recent) > 1:
        avg_unanswered = sum(h.unanswered_rate for h in recent) / len(recent)
        lines.append(f"- Avg unanswered rate last {len(recent)} runs: {_fmt_percentage(avg_unanswered)}")
    return lines


def build_markdown(subreddit_names: Iterable[str], reports: Dict[str, SubredditReport]) -> str:
    lines = []
    lines.append("# Weekly Community Health Summary")
    lines.append(f"_Generated on {datetime.now(timezone.utc).date()}_")

    for name in subreddit_names:
        report = reports[name]
        metrics = report.metrics

        lines.append(f"\n## {name}")

        # Decide which sections to show; default to all if not provided.
        include_sections: Dict[str, bool] = getattr(report, "include_sections", {}) or {
            "stats": True,
            "trends": True,
            "top_posts": True,
            "unanswered": True,
        }

        if include_sections.get("stats", True):
            lines.append("### Stats")
            lines.append(f"- Posts this week: {metrics.total_posts}")
            lines.append(f"- Unanswered rate: {_fmt_percentage(metrics.unanswered_rate) if metrics.total_posts else 'n/a'}")
            ttf = (
                _fmt_minutes(metrics.median_time_to_first_comment_minutes)
                if metrics.median_time_to_first_comment_minutes is not None
                else "n/a"
            )
            lines.append(f"- Median time to first comment: {ttf}")
            lines.append(f"- Post type mix: {_fmt_top_items(metrics.post_type_mix)}")
            lines.append(f"- Top flairs: {_fmt_top_items(metrics.flair_distribution)}")

        if include_sections.get("trends", True):
            lines.append("### Trends vs previous week")
            lines.extend(_format_trends(report.trends))
            lines.append("")
            lines.append("### Recent history (last runs)")
            lines.extend(_format_history(getattr(report, "history", [])))

        if include_sections.get("top_posts", True):
            lines.append("### Top posts this week")
            if not report.top_posts:
                lines.append("- No data")
            else:
                for post in report.top_posts:
                    lines.append(
                        f"- [{post.title}]({post.permalink}) | score: {post.score} | comments: {post.comments}"
                    )

        if include_sections.get("top_posts", True):
            lines.append("### Rising posts (score velocity)")
            if not report.rising_posts:
                lines.append("- None detected")
            else:
                for post in report.rising_posts:
                    lines.append(
                        f"- [{post.title}]({post.permalink}) | score: {post.score} | comments: {post.comments}"
                    )

        if include_sections.get("unanswered", True):
            lines.append("### Unanswered recent posts")
            lines.extend(_format_unanswered(report.unanswered))
            lines.append("### Aging unanswered (48-120h)")
            lines.extend(_format_unanswered(getattr(report, "aging_unanswered", [])))
    return "\n".join(lines)


def write_output(output_dir: Path, markdown: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"summary_{datetime.now().date()}.md"
    out_path.write_text(markdown, encoding="utf-8")
    return out_path
