print("🔥 TikTok Content Radar Started")

import os
import requests
import time

RAPID_API_KEY = os.getenv("RAPID_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

KEYWORDS = [
    "perfume",
    "perfume compliment",
    "how to smell good",
    "that girl routine",
    "office life",
    "working woman",
    "女生生活",
    "打工人",
    "精致生活"
]

MIN_LIKE = 1000
MIN_COMMENT = 10
MAX_RESULTS = 10   # 👉 每天最多推10条


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


# ===== 简单评分（排序用）=====
def score_video(v):
    return v["like"] + (v["comment"] * 5)


# ===== 改编建议（核心🔥）=====
def generate_insight(v):
    title = (v["title"] or "").lower()

    if "office" in title or "work" in title:
        return "👉 改：KL打工人女生 + 用香味提升状态"

    if "routine" in title:
        return "👉 改：女生日常 → 加一个“变好闻”的关键点"

    if "girl" in title or "女生" in title:
        return "👉 改：强调“被注意 / 被记住”"

    if "perfume" in title or "smell" in title:
        return "👉 改：男生视角 + 什么味道更吸引人"

    return "👉 改：加入“女生情绪 + 吸引力 + 办公室场景”"


# ===== 抓数据 =====
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

    items = data.get("data", {}).get("videos", [])

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

    if not all_videos:
        send_telegram("❌ 今天没有抓到内容")
        return

    # 👉 排序（爆款优先）
    all_videos.sort(key=score_video, reverse=True)

    # 👉 去重
    seen = set()
    final_list = []

    for v in all_videos:
        if v["url"] in seen:
            continue
        seen.add(v["url"])
        final_list.append(v)

    # 👉 限制数量
    final_list = final_list[:MAX_RESULTS]

    # 👉 推送
    for v in final_list:
        msg = f"""🔥 今日内容灵感

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
