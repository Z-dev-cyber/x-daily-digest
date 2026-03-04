from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError

import config

logger = logging.getLogger(__name__)

BEIJING_TZ = timezone(timedelta(hours=8))
WECOM_WEBHOOK = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send"
TELEGRAPH_API = "https://api.telegra.ph"


def _telegraph_request(method: str, **params) -> dict:
    from urllib.parse import urlencode
    url = f"{TELEGRAPH_API}/{method}"
    payload = urlencode(params).encode("utf-8")
    req = Request(url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(f"Telegraph API 错误: {result.get('error')}")
    return result["result"]


def _inline_to_nodes(text: str) -> list:
    """Parse inline markdown (bold, links) into Telegraph node children."""
    nodes: list = []
    pattern = re.compile(r"(\*\*(.+?)\*\*|\[(.+?)\]\((.+?)\))")
    last = 0
    for m in pattern.finditer(text):
        if m.start() > last:
            nodes.append(text[last:m.start()])
        if m.group(2):
            nodes.append({"tag": "strong", "children": [m.group(2)]})
        elif m.group(3):
            nodes.append({"tag": "a", "attrs": {"href": m.group(4)}, "children": [m.group(3)]})
        last = m.end()
    if last < len(text):
        nodes.append(text[last:])
    return nodes if nodes else [text]


def _md_to_nodes(md: str) -> list[dict]:
    """Convert markdown to Telegraph Node array."""
    lines = md.split("\n")
    nodes: list[dict] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("## "):
            nodes.append({"tag": "h3", "children": _inline_to_nodes(stripped[3:])})
        elif stripped.startswith("# "):
            nodes.append({"tag": "h3", "children": _inline_to_nodes(stripped[2:])})
        elif stripped.startswith("---"):
            nodes.append({"tag": "hr"})
        elif stripped.startswith("- "):
            children = _inline_to_nodes(stripped[2:])
            children.insert(0, "• ")
            nodes.append({"tag": "p", "children": children})
        elif stripped.startswith("> "):
            nodes.append({"tag": "blockquote", "children": _inline_to_nodes(stripped[2:])})
        else:
            nodes.append({"tag": "p", "children": _inline_to_nodes(stripped)})

    return nodes


def publish_telegraph(title: str, detail_md: str) -> str:
    """Publish detailed analysis to Telegraph, return the URL."""
    logger.info("正在发布详细解读到 Telegraph...")

    account = _telegraph_request(
        "createAccount",
        short_name="XDailyDigest",
        author_name="X Daily Digest",
    )
    token = account["access_token"]

    content_nodes = _md_to_nodes(detail_md)

    page = _telegraph_request(
        "createPage",
        access_token=token,
        title=title,
        content=json.dumps(content_nodes),
        author_name="X Daily Digest",
    )

    url = page["url"]
    logger.info("Telegraph 文章已发布: %s", url)
    return url


def build_message(brief: str, article_url: str) -> str:
    today = datetime.now(BEIJING_TZ).strftime("%Y年%m月%d日")

    return f"""**加密货币 KOL 每日精选**
<font color="comment">{today}</font>

{brief}

👉 [查看详细解读]({article_url})

<font color="comment">由 X Daily Digest 自动生成 · 内容经 AI 筛选总结，请以原文为准</font>"""


def _send_one(url: str, content: str) -> None:
    payload = json.dumps({
        "msgtype": "markdown",
        "markdown": {"content": content},
    }).encode("utf-8")

    req = Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")

    with urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    if result.get("errcode") != 0:
        raise RuntimeError(
            f"企业微信推送失败: [{result.get('errcode')}] {result.get('errmsg')}"
        )


def send_wechat(title: str, content: str) -> None:
    """Push a markdown message to a WeCom group via webhook bot."""
    url = f"{WECOM_WEBHOOK}?key={config.WECOM_WEBHOOK_KEY}"

    logger.info("正在通过企业微信群机器人推送...")

    try:
        _send_one(url, content)
    except URLError as e:
        raise RuntimeError(f"企业微信 Webhook 请求失败: {e}") from e

    logger.info("企业微信群推送成功")
