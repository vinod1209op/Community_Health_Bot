import praw

from ..config.settings import Settings


def create_reddit_client(settings: Settings) -> praw.Reddit:
    return praw.Reddit(
        client_id=settings.client_id,
        client_secret=settings.client_secret,
        username=settings.username,
        password=settings.password,
        user_agent=settings.user_agent,
    )
