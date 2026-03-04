"""
X Daily Digest - 每日 X 博主推文摘要推送

Usage:
    python main.py           # 正常运行：抓取 → 总结 → 推送到微信
    python main.py --dry-run # 试运行：抓取 → 总结 → 打印结果（不推送）
"""
from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime, timezone, timedelta

from fetcher import fetch_all
from summarizer import summarize
from notifier import build_message, publish_telegraph, send_wechat

BEIJING_TZ = timezone(timedelta(hours=8))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("x-daily-digest")


async def run(dry_run: bool = False) -> None:
    logger.info("=== X Daily Digest 开始运行 ===")

    # 1. 抓取推文
    logger.info("步骤 1/4: 抓取推文")
    all_tweets = await fetch_all()

    total = sum(len(ut.tweets) for ut in all_tweets)
    logger.info("共获取 %d 位博主的 %d 条推文", len(all_tweets), total)

    # 2. AI 总结
    logger.info("步骤 2/4: AI 生成摘要")
    brief, detail = summarize(all_tweets)

    # 3. 发布详细解读到 Telegraph
    today = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")
    title = f"加密货币 KOL 每日精选 - {today}"

    if dry_run:
        logger.info("步骤 3/4: 试运行模式，跳过 Telegraph 发布")
        logger.info("步骤 4/4: 试运行模式，跳过微信推送")
        print("\n" + "=" * 60)
        print("【微信摘要】")
        print("=" * 60)
        print(brief)
        print("\n" + "=" * 60)
        print("【详细解读】")
        print("=" * 60)
        print(detail)
        print("=" * 60)
    else:
        logger.info("步骤 3/4: 发布详细解读文章")
        article_url = publish_telegraph(title, detail)

        # 4. 推送到微信
        logger.info("步骤 4/4: 推送到微信")
        content = build_message(brief, article_url)
        send_wechat(title, content)

    logger.info("=== X Daily Digest 运行完成 ===")


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    asyncio.run(run(dry_run=dry_run))


if __name__ == "__main__":
    main()
