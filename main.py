print("🔥 TikTok Content Radar Started")

import os
import requests
import time

RAPID_API_KEY = os.getenv("RAPID_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== 用US抓爆款 =====
REGION = "US"

KEYWORDS = [
    "tiktok made me buy it",
    "perfume that gets compliments",
    "how to smell good all day",
    "that girl glow up",
    "office girl routine",
    "lazy girl routine",
    "high maintenance girl"
]

MIN_LIKE = 1000
MIN_COMMENT = 10
MAX_RESULTS = 10


# ===== Telegram =====
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ telegram config missing")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except Exception as e:
        print("❌ telegram error:", e)


# ===== 评分（简单稳定）=====
def score_video(v):
    return v["like"] + (v["comment"] * 5)


# ===== 改编建议（核心）=====
def generate_insight(v):
    title = (v["title"] or "").lower()

    if "office" in title:
        return "👉 改：KL打工人女生 + 上班压力 + 香味提升状态"

    if "routine" in title:
        return "👉 改：女生routine + 加一个“变好闻”的关键点"

    if "girl" in title:
        return "👉 改：强调“被注意 / 被记住 / 有吸引力”"

    if "perfume" in title or "smell" in title:
        return "👉 改：男生视角 + 什么味道更吸引人"

    return "👉 改：加女生情绪 + 办公室 + 吸引力"


# ===== 抓搜索 =====
def search_videos(keyword):
    print(f"🔍 searching: {keyword}")

    url = "https://tiktok-scraper7.p.rapidapi.com/feed/search"

    querystring = {
        "keywords": keyword,
        "count": "5",
        "cursor": "0",
        "region": REGION
    }

    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
    }

    try:
        res = requests.get(url, headers=headers, params=querystring, timeout=20)
        data = res.json()

        print("STATUS:", res.status_code)
        print("RAW:", str(data)[:200])  # 👉 debug用

    except Exception as e:
        print("❌ request error:", e)
        return []

    items = data.get("data", {}).get("videos", [])

    return parse_items(items)


# ===== 抓Trending（备用）=====
def trending_videos():
    print("🔥 fallback to trending")

    url = "https://tiktok-scraper7.p.rapidapi.com/trending"

    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
    }

    try:
        res = requests.get(url, headers=headers, timeout=20)
        data = res.json()

        items = data.get("data", [])

        return parse_items(items)

    except Exception as e:
        print("❌ trending error:", e)
        return []


# ===== 统一解析 =====
def parse_items(items):
    videos = []

    for v in items:
        if not isinstance(v, dict):
            continue

        try:
            url = v.get("play", "") or v.get("url", "")
            title = v.get("title", "") or v.get("desc", "")

            stats = v.get("stats", {}) or {}

            like = stats.get("diggCount", 0)
            comment = stats.get("commentCount", 0)

            if like >= MIN_LIKE and comment >= MIN_COMMENT:
                videos.append({
                    "url": url,
                    "title": title,
                    "like": like,
                    "comment": comment
                })

        except:
            continue

    return videos


# ===== 主逻辑 =====
def main():
    all_videos = []

    for k in KEYWORDS:
        vids = search_videos(k)
        all_videos += vids
        time.sleep(1)

    # 👉 如果search没数据，用trending
    if not all_videos:
        all_videos = trending_videos()

    if not all_videos:
        send_telegram("❌ 今天完全没数据（API可能挂了）")
        return

    # 排序
    all_videos.sort(key=score_video, reverse=True)

    # 去重
    seen = set()
    final_list = []

    for v in all_videos:
        if v["url"] in seen:
            continue
        seen.add(v["url"])
        final_list.append(v)

    final_list = final_list[:MAX_RESULTS]

    # 推送
    for v in final_list:
        msg = f"""🔥 今日爆款灵感

👍 {v['like']} | 💬 {v['comment']}

📝 {v['title']}

{generate_insight(v)}

🔗 {v['url']}
"""
        send_telegram(msg)
        time.sleep(1)

    print("🔥 Radar finished")


if __name__ == "__main__":
    main()
