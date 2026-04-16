print("🔥 content system started")

import os
import requests
import time
import random

# ===== 配置 =====
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== 你的目标人群关键词（已优化）=====
KEYWORDS = [
    # 英文（全球趋势）
    "self care routine",
    "day in my life",
    "glow up",
    "that girl routine",
    "work life balance",

    # 中文（更贴近亚洲）
    "女生生活",
    "打工人日常",
    "治愈日常",
    "护肤分享",
    "香水推荐",

    # 马来/本地感
    "daily routine girl",
    "aesthetic life",
]

# ===== Telegram =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg[:4000]  # 防止超长
    })


# ===== TikTok API =====
def search_videos(keyword):
    print(f"🔍 {keyword}")

    url = "https://tiktok-scraper7.p.rapidapi.com/feed/search"

    querystring = {
        "keywords": keyword,
        "count": "3",
        "region": "MY",      # 👉 马来西亚
        "publish_time": "1"  # 👉 最新
    }

    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
    }

    try:
        res = requests.get(url, headers=headers, params=querystring, timeout=20)
        data = res.json()
        return data.get("data", [])
    except:
        print("❌ API error")
        return []


# ===== 筛选（你的人群核心）=====
def is_target(v):
    caption = v.get("title", "").lower()

    # ❌ 不要的（娱乐/无关）
    bad = ["funny", "meme", "prank", "game", "football", "cat"]

    # ✅ 你要的（成长 + 情绪 + 女生）
    good = [
        "routine", "life", "self", "care",
        "glow", "vlog", "day",
        "生活", "日常", "女生", "护肤", "香水", "治愈"
    ]

    if any(b in caption for b in bad):
        return False

    if any(g in caption for g in good):
        return True

    return False


# ===== 内容分析（核心价值）=====
def build_content(v):
    author = v.get("author", {}).get("nickname", "")
    uid = v.get("author", {}).get("unique_id", "")
    caption = v.get("title", "")
    likes = v.get("digg_count", 0)
    comments = v.get("comment_count", 0)
    video_id = v.get("aweme_id")

    link = f"https://www.tiktok.com/@{uid}/video/{video_id}"

    # ===== 类型判断 =====
    idea = "生活记录"
    if "routine" in caption.lower():
        idea = "日常变美"
    elif "香水" in caption or "perfume" in caption.lower():
        idea = "精致消费"
    elif "压力" in caption or "stress" in caption.lower():
        idea = "情绪陪伴"

    # ===== 输出内容（重点）=====
    return f"""
🔥 今日选题灵感

👤 作者: {author}
📝 标题: {caption}

❤️ {likes} ｜💬 {comments}

🎯 内容类型: {idea}

———

✨ 为什么会爆：
1️⃣ 真实打工人状态（共鸣）
2️⃣ 低门槛可模仿
3️⃣ 情绪价值（治愈/放松）

———

🎬 你可以这样拍（直接用）：

👉 标题：
“下班后的我，只靠这个救命…”

👉 开头（3秒钩子）：
“今天真的累到不想说话…”

👉 中间：
- 回家
- 洗澡 / 护肤 / 喷香水
- 放松过程

👉 结尾：
“这就是我每天最期待的10分钟”

———

💰 可带产品：
香水 / 护肤 / 情绪消费

🔗 {link}
"""


# ===== 主流程 =====
def main():
    if not RAPID_API_KEY:
        print("❌ Missing RAPID_API_KEY")
        return

    all_videos = []

    for k in KEYWORDS:
        videos = search_videos(k)
        all_videos += videos
        time.sleep(2)

    print(f"🎥 total: {len(all_videos)}")

    for v in all_videos:
        if not is_target(v):
            print("❌ skip")
            continue

        msg = build_content(v)
        send_telegram(msg)

        time.sleep(random.randint(3,6))

    print("🔥 done")


if __name__ == "__main__":
    main()
