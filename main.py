print("🔥 script started")

import os
import requests
import time

RAPID_API_KEY = os.getenv("RAPID_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 👉 更生活化 + 本地化关键词
KEYWORDS = [
    "skincare",
    "perfume",
    "daily life",
    "vlog",
    "self care",
    "morning routine",
    "night routine",
    "生活日常",
    "女生生活",
    "马来西亚生活",
    "KL vlog",
    "打工人",
    "治愈"
]

# ===== Telegram =====
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ telegram config missing")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })


# ===== 抓数据（兼容所有奇怪格式）=====
def search_videos(keyword):
    print(f"🔍 searching: {keyword}")

    url = "https://tiktok-scraper7.p.rapidapi.com/feed/search"

    querystring = {
        "keywords": keyword,
        "count": "5",
        "cursor": "0",
        "region": "MY"
    }

    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
    }

    try:
        res = requests.get(url, headers=headers, params=querystring, timeout=20)
        data = res.json()
    except Exception as e:
        print("❌ request error:", e)
        return []

    videos = []

    # 👉 关键：防止结构变化
    items = data.get("data", {}).get("videos", [])

    if not isinstance(items, list):
        print("❌ unexpected structure")
        return []

    for v in items:

        # 👉 有些API返回是string，直接跳过
        if not isinstance(v, dict):
            continue

        try:
            video_url = v.get("play", "") or v.get("url", "")

            author = ""
            if isinstance(v.get("author"), dict):
                author = v.get("author", {}).get("nickname", "")

            title = v.get("title", "") or v.get("desc", "")

            stats = v.get("stats", {})

            like = stats.get("diggCount", 0)
            comment = stats.get("commentCount", 0)

            if video_url:
                videos.append({
                    "url": video_url,
                    "author": author,
                    "title": title,
                    "like": like,
                    "comment": comment
                })

        except Exception as e:
            print("⚠️ skip one:", e)
            continue

    print(f"🎥 found {len(videos)} videos")
    return videos


# ===== 主逻辑 =====
def main():
    all_videos = []

    for k in KEYWORDS:
        vids = search_videos(k)
        all_videos += vids
        time.sleep(2)

    print(f"🚀 total videos: {len(all_videos)}")

    if len(all_videos) == 0:
        send_telegram("❌ 今天没有抓到任何 TikTok 数据（API可能挂了）")
        return

    # 👉 去重
    seen = set()

    for v in all_videos:
        if v["url"] in seen:
            continue

        seen.add(v["url"])

        msg = f"""🔥 TikTok 视频

👤 作者: {v['author']}
📝 标题: {v['title']}

👍 {v['like']} | 💬 {v['comment']}

🔗 {v['url']}
"""

        send_telegram(msg)
        time.sleep(2)

    print("🔥 script finished")


if __name__ == "__main__":
    main()
