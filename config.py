import os
from dotenv import load_dotenv

load_dotenv()


def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(f"缺少必需的环境变量: {key}")
    return value


X_ACCOUNTS: list[str] = [
    a.strip()
    for a in _require_env("X_ACCOUNTS").split(",")
    if a.strip()
]

LLM_API_KEY = _require_env("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

WECOM_WEBHOOK_KEY = _require_env("WECOM_WEBHOOK_KEY")

COOKIES_FILE = os.getenv("COOKIES_FILE", "cookies.json")
TWEET_FETCH_COUNT = int(os.getenv("TWEET_FETCH_COUNT", "40"))
