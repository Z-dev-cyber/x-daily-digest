from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from twikit import Client

import config

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 5


@dataclass
class TweetData:
    tweet_id: str
    text: str
    created_at: datetime
    author_name: str
    author_screen_name: str
    favorite_count: int = 0
    retweet_count: int = 0
    view_count: int | None = None
    is_quote: bool = False
    quoted_text: str | None = None
    url: str = ""


@dataclass
class UserTweets:
    screen_name: str
    display_name: str
    tweets: list[TweetData] = field(default_factory=list)


def _load_cookies(client: Client) -> None:
    """Load cookies from file. Supports both twikit format and Playwright export."""
    if not os.path.exists(config.COOKIES_FILE):
        logger.error("Cookie 文件不存在: %s", config.COOKIES_FILE)
        logger.error("请先运行 setup_cookies.py 获取 cookie")
        sys.exit(1)

    with open(config.COOKIES_FILE) as f:
        data = json.load(f)

    if isinstance(data, dict):
        client.set_cookies(data)
        logger.info("从 %s 加载了 %d 个 cookie", config.COOKIES_FILE, len(data))
    elif isinstance(data, list):
        cookie_dict = {
            c["name"]: c["value"]
            for c in data
            if ".x.com" in c.get("domain", "") or ".twitter.com" in c.get("domain", "")
        }
        client.set_cookies(cookie_dict)
        logger.info("从 %s 加载了 %d 个 cookie", config.COOKIES_FILE, len(cookie_dict))
    else:
        logger.error("无法识别的 cookie 文件格式")
        sys.exit(1)


def _tweet_url(screen_name: str, tweet_id: str) -> str:
    return f"https://x.com/{screen_name}/status/{tweet_id}"


def _create_client() -> Client:
    proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("ALL_PROXY")
    kwargs: dict = {
        "language": "en-US",
        "user_agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
    }
    if proxy:
        kwargs["proxy"] = proxy
        logger.info("使用代理: %s", proxy)
    return Client(**kwargs)


async def fetch_user_tweets(
    client: Client,
    screen_name: str,
    hours: int = 24,
) -> UserTweets:
    """Fetch a user's original tweets from the last `hours` hours."""
    logger.info("正在获取 @%s 的推文...", screen_name)

    user = await client.get_user_by_screen_name(screen_name)
    tweets_result = await client.get_user_tweets(
        user.id, "Tweets", count=config.TWEET_FETCH_COUNT
    )

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    collected: list[TweetData] = []

    for tweet in tweets_result:
        if tweet.retweeted_tweet is not None:
            continue

        created = tweet.created_at_datetime
        if created and created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        if created and created < cutoff:
            continue

        td = TweetData(
            tweet_id=tweet.id,
            text=tweet.text or "",
            created_at=created or datetime.now(timezone.utc),
            author_name=user.name or screen_name,
            author_screen_name=screen_name,
            favorite_count=tweet.favorite_count or 0,
            retweet_count=tweet.retweet_count or 0,
            view_count=tweet.view_count,
            is_quote=tweet.is_quote_status or False,
            quoted_text=tweet.quote.text if tweet.quote else None,
            url=_tweet_url(screen_name, tweet.id),
        )
        collected.append(td)

    logger.info("@%s: 获取到 %d 条推文", screen_name, len(collected))
    return UserTweets(
        screen_name=screen_name,
        display_name=user.name or screen_name,
        tweets=collected,
    )


async def fetch_all(accounts: list[str] | None = None) -> list[UserTweets]:
    """Fetch tweets for all configured accounts with retry on failure."""
    accounts = accounts or config.X_ACCOUNTS

    results: list[UserTweets] = []
    for account in accounts:
        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                client = _create_client()
                _load_cookies(client)
                ut = await fetch_user_tweets(client, account)
                results.append(ut)
                success = True
                break
            except Exception:
                if attempt < MAX_RETRIES:
                    logger.warning(
                        "获取 @%s 失败 (第%d次)，%d秒后重试...",
                        account, attempt, RETRY_DELAY,
                    )
                    await asyncio.sleep(RETRY_DELAY)
                else:
                    logger.exception("获取 @%s 推文失败 (已重试%d次)", account, MAX_RETRIES)

        if not success:
            results.append(UserTweets(screen_name=account, display_name=account))

        await asyncio.sleep(2)

    return results
