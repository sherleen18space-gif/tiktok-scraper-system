print("🔥 script started")

import os
import requests
import time
import random

# ===== 配置 =====
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 👉 关键词（生活化 + 人设）
KEYWORDS = [
    "daily life",
    "self care",
    "skincare",
    "perfume",
    "work life",
    "office life",
    "生活日常",
    "女生生活",
    "打工人",
    "vlog"
]

# ===== 搜索视频 =====
def search_videos(keyword):
    print(f"🔍 searching: {keyword}")

    url = "https://tiktok-scraper7.p.rapidapi.com/feed/search"

    querystring = {
        "keywords": keyword,
        "count": "5"
    }

    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
    }

    try:
        res = requests.get(url, headers=headers, params=querystring)
        data = res.json()
    except:
        print("❌ API error")
        return []

    if "data" not in data or not isinstance(data["data"], list):
        print("❌ no valid data")
        return []

    videos = []

    for v in data["data"]:
        try:
            author = v.get("author", {})
            stats = v.get("statistics", {})

            like = stats.get("digg_count") or v.get("digg_count", 0)
            comment = stats.get("comment_count") or v.get("comment_count", 0)
            play = stats.get("play_count") or v.get("play_count", 0)

            title = v.get("title") or v.get("desc") or ""

            # ❌ 没有ID直接跳过
            if not author.get("unique_id") or not v.get("aweme_id"):
                continue

            video = {
                "url": f"https://www.tiktok.com/@{author.get('unique_id')}/video/{v.get('aweme_id')}",
                "author": author.get("nickname", ""),
                "username": author.get("unique_id", ""),
                "title": title,
                "like": like,
                "comment": comment,
                "play": play
            }

            # 👉 过滤
            if not is_target(video):
                continue

            videos.append(video)

        except:
            continue

    print(f"🎥 usable videos: {len(videos)}")
    return videos


# ===== 过滤逻辑（关键）=====
def is_target(v):
    title = v["title"].lower()

    bad_words = [
        "funny", "meme", "prank",
        "cat", "dog", "animal",
        "rural", "village",
        "philippines", "india"
    ]

    if any(x in title for x in bad_words):
        return False

    # 👉 不要太高门槛（真实生活通常不爆）
    if v["like"] < 100:
        return False

    good_words = [
        "routine", "day", "vlog",
        "self", "life", "work",
        "skincare", "perfume",
        "生活", "女生", "日常", "上班"
    ]

    if not any(x in title for x in good_words):
        return False

    return True


# ===== 内容类型 =====
def detect_type(title):
    t = title.lower()

    if any(x in t for x in ["vlog", "day", "生活", "日常"]):
        return "真实生活"

    if any(x in t for x in ["heal", "relax", "治愈", "压力"]):
        return "情绪陪伴"

    if any(x in t for x in ["glow", "improve", "变好"]):
        return "成长变好"

    if any(x in t for x in ["skincare", "perfume", "护肤", "香水"]):
        return "产品种草"

    return "其他"


# ===== 爆点分析 =====
def analyze(v):
    hooks = []

    if any(x in v["title"].lower() for x in ["routine", "day", "vlog"]):
        hooks.append("可复制日常")

    if v["like"] > 5000:
        hooks.append("高点赞")

    if v["comment"] > 100:
        hooks.append("互动强")

    return " + ".join(hooks) if hooks else "普通结构"


# ===== Telegram =====
def send_telegram(v):
    msg = f"""
🔥 内容参考

👤 {v['author']} (@{v['username']})
📝 {v['title']}

👍 {v['like']} | 💬 {v['comment']} | ▶️ {v['play']}

📊 类型: {detect_type(v['title'])}
🧠 爆点: {analyze(v)}

🔗 {v['url']}
"""

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )


# ===== 主流程 =====
def main():
    all_videos = []

    for k in KEYWORDS:
        vids = search_videos(k)
        all_videos += vids
        time.sleep(1)

    print(f"🚀 total usable videos: {len(all_videos)}")

    sent = 0

    for v in all_videos:
        send_telegram(v)
        sent += 1

        time.sleep(random.randint(2, 5))

    print(f"✅ sent: {sent}")
    print("🔥 script finished")


if __name__ == "__main__":
    main()
