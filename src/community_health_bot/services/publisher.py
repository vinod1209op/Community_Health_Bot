import praw

from .logging import extract_rate_limit_headers, log_json, setup_logger


def submit_summary(reddit: praw.Reddit, subreddit_name: str, title: str, markdown: str) -> str:
    logger = setup_logger()
    submission = reddit.subreddit(subreddit_name).submit(title=title, selftext=markdown)
    headers = extract_rate_limit_headers(reddit._core._requestor._http.headers) if hasattr(reddit, "_core") else {}
    log_json(logger, "submitted_summary", subreddit=subreddit_name, permalink=submission.permalink, **headers)
    return f"https://reddit.com{submission.permalink}"
