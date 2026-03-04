from __future__ import annotations

import logging
import re

from openai import OpenAI

import config
from fetcher import UserTweets

logger = logging.getLogger(__name__)

SPLIT_MARKER = "===SPLIT==="

SYSTEM_PROMPT = f"""\
你是一位专业的加密货币市场分析师。你需要基于 KOL 推文生成两部分内容，用 {SPLIT_MARKER} 分隔：

【第一部分：微信摘要】（控制在200字以内）
用3-5个要点快速概括今日最值得关注的信息，格式：
> 今日关注
> 1. xxx
> 2. xxx
> 3. xxx

只列最核心的信息，简洁有力。如果有明确交易机会用🔥标注。

{SPLIT_MARKER}

【第二部分：详细解读】（完整的文章内容）
逐条分析每条推文，格式：

## @KOL名

**HH:MM 原文要点**
一两句话概括推文核心内容

**交易机会分析**
- 涉及币种/项目
- 潜在交易方向
- 关键价位/时间
- 风险提示

[序号]

---

最后写一段「今日综合研判」总结整体市场情绪和最值得关注的机会。

规则：
1. 用中文表达，保留关键英文术语
2. 无关内容（日常问候等）标注为「无交易相关」简单带过
3. 每条分析引用对应序号 [序号]
"""


def _build_user_prompt(all_tweets: list[UserTweets]) -> tuple[str, list[str]]:
    """Build user prompt and return (prompt, tweet_urls) for link references."""
    parts: list[str] = []
    urls: list[str] = []
    has_content = False
    idx = 0

    for ut in all_tweets:
        if not ut.tweets:
            continue

        has_content = True
        parts.append(f"\n## @{ut.screen_name} ({ut.display_name})")
        for t in ut.tweets:
            idx += 1
            urls.append(t.url)
            line = f"- [{idx}] [{t.created_at:%H:%M}] {t.text}"
            if t.is_quote and t.quoted_text:
                line += f"\n  > 引用: {t.quoted_text[:200]}"
            line += f"\n  [❤️ {t.favorite_count} | 🔁 {t.retweet_count}]"
            parts.append(line)

    if not has_content:
        return "", []

    prompt = (
        "以下是各位加密货币 KOL 在过去 24 小时内的推文，"
        "请生成微信摘要和详细解读两部分。\n"
        "每条推文前的 [数字] 是序号，请在分析中引用对应序号。\n"
        + "\n".join(parts)
    )
    return prompt, urls


def _replace_refs(text: str, urls: list[str]) -> str:
    """Replace [N] references with clickable links."""
    def _replace(m: re.Match) -> str:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(urls):
            return f"[原文]({urls[idx]})"
        return m.group(0)

    return re.sub(r"\[(\d+)\]", _replace, text)


def summarize(all_tweets: list[UserTweets]) -> tuple[str, str]:
    """Generate brief summary + detailed analysis. Returns (brief, detail)."""
    user_prompt, urls = _build_user_prompt(all_tweets)

    if not user_prompt:
        logger.info("所有 KOL 在过去24小时内均无推文")
        empty = "过去 24 小时内，您关注的 KOL 均未发布新推文。"
        return empty, empty

    logger.info("正在调用 %s 生成摘要...", config.LLM_MODEL)

    client = OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)
    response = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    result = response.choices[0].message.content or "（AI 未返回内容）"
    parts = result.split(SPLIT_MARKER, 1)

    brief = parts[0].strip()
    detail = parts[1].strip() if len(parts) > 1 else result

    detail = _replace_refs(detail, urls)

    logger.info("摘要生成完成: 简报 %d 字, 详细 %d 字", len(brief), len(detail))
    return brief, detail
