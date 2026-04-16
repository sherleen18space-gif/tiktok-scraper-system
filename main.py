print("🔥 script started")

import os
import requests
import time
import random

API_KEY = os.getenv("TIKWM_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 👉 内容关键词（生活 + 情绪 + 产品）
KEYWORDS = [
    "skincare",
    "perfume",
    "daily life",
    "vlog",
    "self care",
    "morning routine",
    "女生生活",
    "打工人",
    "马来西亚生活",
    "治愈"
]

# ===== Telegram =====
def send(msg):
    if not TELEGRAM_TOKEN:
        print(msg)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

# ===== 调 TikWM API =====
def search_videos(keyword):
    print(f"🔍 searching: {keyword}")

    url = "https://www.tikwm.com/api/feed/search"

    params = {
        "keywords": keyword,
        "count": 5,
        "cursor": 0,
        "hd": 1
    }

    try:
        r = requests.get(url, params=params, timeout=20)
        data = r.json()
    except:
        print("❌ request failed")
        return []

    if "data" not in data:
        print("❌ no data")
        return []

    videos = []

    for v in data["data"]:
        videos.append({
            "author": v.get("author", {}).get("nickname", ""),
            "title": v.get("title", ""),
            "like": v.get("digg_count", 0),
            "comment": v.get("comment_count", 0),
            "play": v.get("play_count", 0),
            "url": f"https://www.tiktok.com/@{v.get('author', {}).get('unique_id','')}/video/{v.get('video_id','')}"
        })

    return videos

# ===== 内容判断 =====
def is_good(video):
    title = video["title"].lower()

    signals = [
        "routine",
        "vlog",
        "day",
        "生活",
        "治愈",
        "分享",
        "日常",
        "self care"
    ]

    # 👉 至少有内容关键词
    if not any(s in title for s in signals):
        return False

    # 👉 基本互动
    if video["like"] < 1000:
        return False

    return True

# ===== 爆点分析 =====
def analyze(video):
    title = video["title"].lower()

    hook = "未知"

    if "routine" in title:
        hook = "日常流程（容易复制）"
    elif "vlog" in title:
        hook = "真实生活感"
    elif "治愈" in title:
        hook = "情绪陪伴"
    elif "skincare" in title:
        hook = "变美焦虑"
    elif "perfume" in title:
        hook = "气味记忆 + 气质标签"

    return hook

# ===== 主流程 =====
def main():
    all_videos = []

    for k in KEYWORDS:
        all_videos += search_videos(k)
        time.sleep(random.randint(2,4))

    print(f"🚀 total: {len(all_videos)}")

    for v in all_videos:
        if not is_good(v):
            continue

        insight = analyze(v)

        msg = f"""
🔥 TikTok内容参考

👤 作者: {v['author']}
📝 标题: {v['title']}

👍 {v['like']} | 💬 {v['comment']}

🧠 爆点: {insight}

🔗 {v['url']}
"""

        send(msg)

        time.sleep(random.randint(2,4))

    print("🔥 script finished")

if __name__ == "__main__":
    main()
