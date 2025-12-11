import json
from typing import Optional

import requests


def send_webhook(webhook_url: Optional[str], title: str, content: str) -> None:
    if not webhook_url:
        return
    excerpt = content if len(content) <= 1800 else content[:1800] + "\n…(truncated)"
    payload = {
        # Slack-compatible
        "text": f"*{title}*\n{excerpt}",
        # Discord-compatible
        "content": f"**{title}**\n{excerpt}",
    }
    headers = {"Content-Type": "application/json"}
    try:
        requests.post(webhook_url, data=json.dumps(payload), headers=headers, timeout=5)
    except Exception:
        # Fail silently to avoid interrupting main flow.
        return
