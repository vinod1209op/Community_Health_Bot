import json
import logging
from typing import Any, Dict, Optional


def setup_logger(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("community_health_bot")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


def log_json(logger: logging.Logger, message: str, **fields: Any) -> None:
    payload: Dict[str, Any] = {"msg": message, **fields}
    logger.info(json.dumps(payload))


def extract_rate_limit_headers(response) -> Dict[str, Any]:
    headers = getattr(response, "headers", {}) or {}
    return {
        "x_ratelimit_used": headers.get("X-Ratelimit-Used"),
        "x_ratelimit_remaining": headers.get("X-Ratelimit-Remaining"),
        "x_ratelimit_reset": headers.get("X-Ratelimit-Reset"),
    }


def log_rate_limit(logger: logging.Logger, reddit) -> None:
    """
    Best-effort logging of rate limit headers from the underlying PRAW requestor.
    """
    try:
        response = getattr(getattr(getattr(reddit, "_core", None), "_requestor", None), "_http", None)
        headers = extract_rate_limit_headers(response)
        if any(headers.values()):
            log_json(logger, "rate_limit_status", **headers)
    except Exception:
        return
