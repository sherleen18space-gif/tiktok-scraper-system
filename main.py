print("🔥 TikTok Content Radar Started")

import os
import requests
import time

RAPID_API_KEY = os.getenv("RAPID_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ✅ 核心：用“稳定出数据关键词”
KEYWORDS = [
    "makeup",
    "skincare routine",
    "grwm",
    "ootd",
    "morning routine",
    "night routine",
    "beauty tips"
]

# 👉 fallback（保证永远有数据）
FALLBACK_KEYWORD = "makeup"

MIN_LIKE = 500
MIN_COMMENT = 5
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


# ===== 简单评分 =====
def score_video(v):
    return v["like"] + (v["comment"] * 3)


# ===== 改编提示（卖货关键）=====
def generate_insight(v):
    return """👉 改成你的版本：
1. 换成 KL上班女生
2. 加“很累 / 没人注意”的情绪
3. 用“香味”作为改变点
4. 结果：被注意 / 被记住"""


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

        print("STATUS:", res.status_code)

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

        # 👉 fallback：如果这个keyword没数据
        if not vids:
            print(f"⚠️ fallback for {k}")
            vids = search_videos(FALLBACK_KEYWORD)

        all_videos += vids
        time.sleep(1)

    if not all_videos:
        send_telegram("❌ 今天完全没数据（API异常）")
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
        time.sleep(1)

    print("🔥 Radar finished")


if __name__ == "__main__":
    main()
