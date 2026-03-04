# X Daily Digest

每天自动抓取你关注的 X/Twitter 博主推文，通过 AI 总结关键内容，并推送到你的微信。

## 功能

- 自动抓取指定 X 博主过去 24 小时的推文
- 使用 DeepSeek（或 OpenAI）生成中文摘要（按博主分组，提取关键观点）
- 通过 PushPlus 推送 Markdown 格式的摘要到微信
- 通过 GitHub Actions 每天北京时间 10:00 自动运行
- 支持手动触发和本地调试

## 快速开始

### 1. 准备凭据

你需要准备以下信息：

| 凭据 | 说明 | 获取方式 |
|------|------|----------|
| X Cookie | auth_token 和 ct0 | 从 Chrome DevTools 复制（见下方） |
| DeepSeek API Key | 用于 AI 总结 | [platform.deepseek.com](https://platform.deepseek.com/) |
| PushPlus Token | 用于微信推送 | [www.pushplus.plus](https://www.pushplus.plus/)，微信扫码即可 |

**获取 PushPlus Token：**

1. 用微信扫码登录 [pushplus.plus](https://www.pushplus.plus/)
2. 登录后在首页即可看到你的 **token**
3. 复制保存这个 token

**获取 X Cookie：**

1. 打开 Chrome 浏览器，确保已登录 x.com
2. 按 `Cmd + Option + I` 打开开发者工具
3. 点击 **Application** 标签页
4. 左侧栏找到 **Cookies → https://x.com**
5. 复制 `auth_token` 和 `ct0` 的值
6. 运行 `python3.11 setup_cookies.py` 并粘贴

### 2. 本地运行

```bash
# 克隆项目
git clone <your-repo-url>
cd x-daily-digest

# 安装依赖
pip install -r requirements.txt

# 复制并编辑配置文件
cp .env.example .env
# 编辑 .env 填入你的凭据

# 提取 X Cookie
python3.11 setup_cookies.py

# 试运行（不推送微信，仅打印结果）
python3.11 main.py --dry-run

# 正式运行（推送到微信）
python3.11 main.py
```

### 3. 部署到 GitHub Actions

1. 将代码推送到 GitHub 仓库

2. 在仓库的 **Settings → Secrets and variables → Actions** 中添加以下 Secrets：

   | Secret 名称 | 值 |
   |---|---|
   | `X_ACCOUNTS` | 关注的博主列表，逗号分隔，如 `elonmusk,sama,karpathy` |
   | `LLM_API_KEY` | DeepSeek API Key |
   | `LLM_BASE_URL` | `https://api.deepseek.com`（可选） |
   | `LLM_MODEL` | `deepseek-chat`（可选） |
   | `PUSHPLUS_TOKEN` | PushPlus Token |

3. 工作流会在每天北京时间 10:00 自动运行

4. 你也可以在 **Actions** 页面手动触发运行进行测试

## 配置说明

| 环境变量 | 必填 | 默认值 | 说明 |
|---------|------|--------|------|
| `X_ACCOUNTS` | 是 | - | 博主列表，逗号分隔 |
| `LLM_API_KEY` | 是 | - | DeepSeek / OpenAI API 密钥 |
| `LLM_BASE_URL` | 否 | `https://api.deepseek.com` | LLM API 地址 |
| `LLM_MODEL` | 否 | `deepseek-chat` | LLM 模型名称 |
| `PUSHPLUS_TOKEN` | 是 | - | PushPlus 微信推送 Token |
| `TWEET_FETCH_COUNT` | 否 | `40` | 每个博主获取的推文数量 |

## 项目结构

```
x-daily-digest/
├── main.py              # 主程序入口
├── fetcher.py           # X 推文抓取（使用 twikit）
├── summarizer.py        # AI 内容总结（DeepSeek / OpenAI）
├── notifier.py          # 微信推送（PushPlus）
├── config.py            # 环境变量配置
├── setup_cookies.py     # X Cookie 提取工具
├── requirements.txt     # Python 依赖
├── .env.example         # 环境变量模板
├── .gitignore
└── .github/workflows/
    └── daily-digest.yml # GitHub Actions 定时任务
```

## 成本估算

- **X 数据抓取**：免费（twikit 基于 cookie 会话）
- **DeepSeek API**：约 ¥0.01/天（deepseek-chat，视推文数量）
- **PushPlus**：免费（每天 200 次推送额度）
- **GitHub Actions**：免费（公开仓库无限制，私有仓库每月 2000 分钟免费额度）

## 注意事项

- twikit 基于网页会话，X 平台更新可能导致临时不可用，请关注 [twikit 仓库](https://github.com/d60/twikit) 获取更新
- X Cookie 有效期有限（通常数月），失效后需重新提取
- 建议使用小号登录 X，避免主账号受到风控影响
- PushPlus 免费用户每天限 200 次推送，对于每日摘要完全够用
