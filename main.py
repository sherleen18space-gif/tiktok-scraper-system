print("🔥 TikTok Content Radar Started")

import os
import requests
import time

RAPID_API_KEY = os.getenv("RAPID_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 👉 用你原本“能跑”的关键词逻辑 + 升级
KEYWORDS = [
    "daily life",
    "self care",
    "skincare",
    "perfume",
    "work life",
    "office life",
    "生活日常",
    "女生生活"
]

MIN_LIKE = 500
MIN_COMMENT = 5
MAX_RESULTS = 15


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


# ===== 评分（简单有效）=====
def score_video(v):
    return v["like"] + (v["comment"] * 3)


# ===== 改编提示（重点🔥）=====
def generate_insight(v):
    return """👉 改法：
1. 换成 KL女生 / 打工人
2. 加一个“被注意 / 被记住”的瞬间
3. 用香味当转变点"""


# ===== 抓数据（你原本稳定版本）=====
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
        print("❌ error:", e)
        return []

    items = data.get("data", {}).get("videos", [])

    videos = []

    for v in items:
        if not isinstance(v, dict):
            continue

        try:
            video_url = v.get("play", "") or v.get("url", "")
            title = v.get("title", "") or v.get("desc", "")

            stats = v.get("stats", {}) or {}

            like = stats.get("diggCount", 0)
            comment = stats.get("commentCount", 0)

            if like >= MIN_LIKE and comment >= MIN_COMMENT:
                videos.append({
                    "url": video_url,
                    "title": title,
                    "like": like,
                    "comment": comment
                })

        except:
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

    if not all_videos:
        send_telegram("❌ 今天没有抓到内容（API正常但无匹配）")
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
        msg = f"""🔥 今日内容灵感

👍 {v['like']} | 💬 {v['comment']}

📝 {v['title']}

{generate_insight(v)}

🔗 {v['url']}
"""
        send_telegram(msg)
        time.sleep(2)

    print("🔥 Radar finished")


if __name__ == "__main__":
    main()
