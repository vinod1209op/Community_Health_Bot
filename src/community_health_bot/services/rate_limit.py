import time
from typing import Optional

from .logging import log_json


def _parse_header_value(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def maybe_backoff_if_low(reddit, logger, remaining_threshold: float = 10.0, buffer_seconds: float = 5.0) -> float:
    """
    Sleep when Reddit rate-limit remaining is low.

    Returns the number of seconds slept (0 if no backoff).
    """
    try:
        response = getattr(getattr(getattr(reddit, "_core", None), "_requestor", None), "_http", None)
        headers = getattr(response, "headers", {}) or {}
        remaining = _parse_header_value(headers.get("X-Ratelimit-Remaining"))
        reset = _parse_header_value(headers.get("X-Ratelimit-Reset"))
        if remaining is None or reset is None:
            return 0.0
        if remaining > remaining_threshold:
            return 0.0
        sleep_for = max(reset + buffer_seconds, buffer_seconds)
        log_json(
            logger,
            "rate_limit_backoff",
            remaining=remaining,
            reset=reset,
            buffer_seconds=buffer_seconds,
            sleep_for=sleep_for,
        )
        time.sleep(sleep_for)
        return sleep_for
    except Exception:
        return 0.0
