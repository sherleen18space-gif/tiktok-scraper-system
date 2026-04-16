print("🔥 content system started")

import os
import requests
import time
import random

# ===== 环境变量 =====
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print("RAPID:", "OK" if RAPID_API_KEY else "MISSING")
print("TG:", "OK" if TELEGRAM_TOKEN else "MISSING")


# ===== 关键词（已优化：生活化 + 情绪 + 女生）=====
KEYWORDS = [
    "day in my life girl",
    "self care routine",
    "after work routine",
    "night routine girl",
    "that girl routine",

    "打工人日常",
    "女生生活",
    "治愈日常",
    "下班生活",
    "护肤分享",
    "香水推荐"
]


# ===== Telegram =====
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Telegram missing")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg[:4000]
    })


# ===== TikTok API =====
def search_videos(keyword):
    print(f"🔍 searching: {keyword}")

    url = "https://tiktok-scraper7.p.rapidapi.com/feed/search"

    querystring = {
        "keywords": keyword,
        "count": "3",
        "region": "MY",       # 👉 马来西亚
        "publish_time": "1"   # 👉 最新
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


# ===== 筛选逻辑（放宽，不会全死）=====
def is_target(v):
    caption = v.get("title", "").lower()

    bad = ["funny", "prank", "meme", "game", "football"]

    if any(b in caption for b in bad):
        return False

    return True  # 👉 放宽（重点！！）


# ===== 内容生成（核心）=====
def build_content(v):
    author = v.get("author", {}).get("nickname", "")
    uid = v.get("author", {}).get("unique_id", "")
    caption = v.get("title", "")
    likes = v.get("digg_count", 0)
    comments = v.get("comment_count", 0)
    video_id = v.get("aweme_id")

    link = f"https://www.tiktok.com/@{uid}/video/{video_id}"

    text = caption.lower()

    # ===== 类型判断 =====
    if "routine" in text:
        idea = "日常变美"
    elif "香水" in caption or "perfume" in text:
        idea = "精致消费"
    elif "压力" in caption or "stress" in text:
        idea = "情绪陪伴"
    else:
        idea = "真实生活"

    # ===== 输出你的内容（核心）=====
    return f"""
🔥 今日可拍内容（直接用）

👤 作者: {author}
📝 标题: {caption}

❤️ {likes} ｜💬 {comments}

🎯 类型: {idea}

———

✨ 为什么会爆：
1️⃣ 打工人共鸣（累 / 压力）
2️⃣ 真实感（不像广告）
3️⃣ 低门槛（人人可模仿）

———

🎬 直接拍这个（照抄都行）：

👉 标题：
“下班后的我，只想这样活…”

👉 开头（3秒）：
“今天真的累到不想讲话…”

👉 中间：
- 回家（画面）
- 洗澡 / 护肤 / 喷香水
- 躺床 / 放松

👉 结尾：
“这是我每天最期待的时刻”

———

💰 可带产品：
香水 / 护肤 / 情绪消费

🔗 {link}
"""


# ===== 主流程 =====
def main():
    if not RAPID_API_KEY:
        print("❌ Missing API KEY")
        return

    all_videos = []

    for k in KEYWORDS:
        videos = search_videos(k)
        all_videos += videos
        time.sleep(2)

    print(f"🎥 total videos: {len(all_videos)}")

    valid_found = False

    for v in all_videos:
        if not is_target(v):
            continue

        valid_found = True
        msg = build_content(v)
        send_telegram(msg)

        time.sleep(random.randint(3,6))

    # ===== fallback（关键）=====
    if not valid_found and len(all_videos) > 0:
        print("⚠️ fallback sending")

        for v in all_videos[:3]:
            msg = build_content(v)
            send_telegram(msg)

    print("🔥 done")


if __name__ == "__main__":
    main()
