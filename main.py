print("🔥 script started")

import os
import requests
import time
import random

# ===== API配置 =====
RAPID_API_KEY = os.getenv("RAPID_API_KEY")

# 👉 TikWM endpoint
BASE_URL = "https://tiktok-scraper7.p.rapidapi.com/feed/search"

HEADERS = {
    "X-RapidAPI-Key": RAPID_API_KEY,
    "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
}

# ===== Telegram =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== 关键词（重点：生活化 + 本地）=====
KEYWORDS = [
    "skincare routine",
    "perfume",
    "daily vlog",
    "day in my life",
    "self care",
    "生活日常",
    "女生生活",
    "治愈",
    "压力",
    "打工人"
]

# ===== 获取视频 =====
def search_videos(keyword):
    print(f"🔍 searching: {keyword}")

    querystring = {
        "keywords": keyword,
        "count": "5",   # 每个关键词拿5个
        "cursor": "0"
    }

    try:
        response = requests.get(BASE_URL, headers=HEADERS, params=querystring)
        data = response.json()
    except:
        print("❌ API error")
        return []

    videos = []

    if "data" in data:
        for v in data["data"]:
            videos.append({
                "url": v.get("play", ""),
                "title": v.get("title", ""),
                "author": v.get("author", {}).get("nickname", ""),
                "like": v.get("digg_count", 0),
                "comment": v.get("comment_count", 0),
                "create_time": v.get("create_time", 0)
            })

    print(f"🎥 found {len(videos)} videos")
    return videos

# ===== 内容筛选 =====
def is_good_video(v):
    text = (v["title"] or "").lower()

    # ❌ 过滤无关内容
    bad_words = ["funny", "game", "meme", "cat", "monkey"]
    if any(b in text for b in bad_words):
        return False

    # ✔ 内容型关键词
    good_words = [
        "routine",
        "day",
        "vlog",
        "life",
        "self",
        "care",
        "study",
        "work",
        "生活",
        "日常",
        "治愈",
        "压力",
        "成长"
    ]

    score = sum(1 for w in good_words if w in text)

    return score >= 1

# ===== 爆款分析 =====
def analyze(v):
    like = v["like"]
    comment = v["comment"]
    text = v["title"]

    hook = "日常记录"
    if "routine" in text.lower():
        hook = "routine吸引"
    if "vlog" in text.lower():
        hook = "真实生活感"
    if "治愈" in text:
        hook = "情绪共鸣"

    return f"""
📌 作者: {v['author']}
🧠 类型: {hook}

🔥 点赞: {like}
💬 评论: {comment}

💡 标题:
{text}

🎯 可做选题:
👉 模仿这个主题拍：{hook}
"""

# ===== Telegram =====
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Telegram skipped")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

# ===== 主流程 =====
def main():
    all_videos = []

    for k in KEYWORDS:
        all_videos += search_videos(k)
        time.sleep(2)

    print(f"🚀 total videos: {len(all_videos)}")

    if len(all_videos) == 0:
        print("❌ no data")
        return

    for v in all_videos:
        if not is_good_video(v):
            print("❌ skip")
            continue

        msg = f"""
🔥 可参考视频

🔗 {v['url']}

{analyze(v)}
"""
        send_telegram(msg)

        time.sleep(random.randint(3,6))

    print("🔥 script finished")


if __name__ == "__main__":
    main()
