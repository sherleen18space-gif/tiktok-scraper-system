print("🔥 script started")

import os
import requests
import time
import random

# ===== API配置 =====
RAPID_API_KEY = os.getenv("RAPID_API_KEY")

BASE_URL = "https://tiktok-scraper7.p.rapidapi.com/search"

HEADERS = {
    "X-RapidAPI-Key": RAPID_API_KEY,
    "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
}

# ===== Telegram =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== 关键词 =====
KEYWORDS = [
   "skincare routine",
    "perfume",
    "daily vlog",
    "self care",
    "生活日常",
    "女生生活",
    "马来西亚生活",
    "KL vlog",
    "上班族",
    "打工人",
    "治愈"
]

# ===== 获取视频 =====
def search_videos(keyword):
    print(f"🔍 searching: {keyword}")

    querystring = {
        "keyword": keyword,
        "count": "5"
    }

    try:
        res = requests.get(BASE_URL, headers=HEADERS, params=querystring)
        data = res.json()
    except Exception as e:
        print("❌ API error:", e)
        return []

    videos = []

    if "data" not in data:
        print("❌ no data")
        return []

    for v in data["data"]:

        videos.append({
            "url": v.get("play", ""),
            "title": v.get("title", ""),
            "author": v.get("author", {}).get("nickname", ""),
            "like": v.get("digg_count", 0),
            "comment": v.get("comment_count", 0)
        })

    print(f"🎥 found {len(videos)} videos")
    return videos


# ===== Telegram =====
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Telegram skipped")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except Exception as e:
        print("❌ telegram error:", e)


# ===== 主流程 =====
def main():
    all_videos = []

    for k in KEYWORDS:
        result = search_videos(k)
        all_videos += result
        time.sleep(2)

    print(f"🚀 total videos: {len(all_videos)}")

    if len(all_videos) == 0:
        send_telegram("❌ 没有抓到任何视频（可能API没额度）")
        return

    for v in all_videos:

        msg = f"""
🔥 TikTok 视频

👤 作者: {v['author']}
📝 标题: {v['title']}

👍 {v['like']} | 💬 {v['comment']}

🔗 {v['url']}
"""

        send_telegram(msg)

        time.sleep(random.randint(2,5))

    print("🔥 script finished")


if __name__ == "__main__":
    main()
