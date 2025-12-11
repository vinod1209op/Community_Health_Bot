import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Sequence

import yaml
from dotenv import load_dotenv


@dataclass
class SubredditConfig:
    name: str
    unanswered_limit: int = 10
    top_posts_limit: int = 10
    include_sections: Dict[str, bool] = field(
        default_factory=lambda: {
            "stats": True,
            "trends": True,
            "top_posts": True,
            "unanswered": True,
        }
    )


@dataclass
class Settings:
    client_id: str
    client_secret: str
    username: str
    password: str
    user_agent: str
    output_dir: Path
    subreddit_configs: Dict[str, SubredditConfig]
    webhook_url: Optional[str] = None


def load_settings(
    env_file: Optional[Path] = None, config_file: Optional[Path] = None, allow_missing: bool = False
) -> Settings:
    if env_file:
        load_dotenv(dotenv_path=env_file)
    else:
        load_dotenv()

    required = [
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USERNAME",
        "REDDIT_PASSWORD",
        "USER_AGENT",
    ]
    missing = [key for key in required if not os.getenv(key)]
    if missing and not allow_missing:
        sys.exit(f"Missing environment variables: {', '.join(missing)}")

    output_dir = Path(os.getenv("OUTPUT_DIR", "./output")).expanduser()
    subreddit_configs = _load_subreddit_configs(config_file)

    return Settings(
        client_id=os.getenv("REDDIT_CLIENT_ID", "mock_client_id" if allow_missing else ""),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET", "mock_client_secret" if allow_missing else ""),
        username=os.getenv("REDDIT_USERNAME", "mock_user" if allow_missing else ""),
        password=os.getenv("REDDIT_PASSWORD", "mock_password" if allow_missing else ""),
        user_agent=os.getenv("USER_AGENT", "server:community-health-bot:mock (by /u/mock)" if allow_missing else ""),
        output_dir=output_dir,
        subreddit_configs=subreddit_configs,
        webhook_url=os.getenv("WEBHOOK_URL"),
    )


def _load_subreddit_configs(config_file: Optional[Path]) -> Dict[str, SubredditConfig]:
    if not config_file:
        return {}
    if not config_file.exists():
        sys.exit(f"Config file not found: {config_file}")
    with config_file.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    configs: Dict[str, SubredditConfig] = {}
    for entry in data.get("subreddits", []):
        name = entry.get("name")
        if not name:
            continue
        include_sections = entry.get("include_sections") or {}
        configs[name] = SubredditConfig(
            name=name,
            unanswered_limit=entry.get("unanswered_limit", 10),
            top_posts_limit=entry.get("top_posts_limit", 10),
            include_sections={
                "stats": include_sections.get("stats", True),
                "trends": include_sections.get("trends", True),
                "top_posts": include_sections.get("top_posts", True),
                "unanswered": include_sections.get("unanswered", True),
            },
        )
    return configs


def validate_user_agent(user_agent: str, allowed_patterns: Optional[Sequence[str]] = None) -> None:
    if not user_agent or "your_bot_username" in user_agent:
        sys.exit("USER_AGENT must be set to a descriptive value (no placeholders).")
    if allowed_patterns:
        if not any(pattern in user_agent for pattern in allowed_patterns):
            sys.exit("USER_AGENT does not match expected format. Example: server:app-name:1.0.0 (by /u/your_bot)")
