print("🔥 script started")

import os
import requests
import time

RAPID_API_KEY = os.getenv("RAPID_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== 配置 =====
KEYWORDS = [
    "how to smell good",
    "perfume compliment",
    "glow up routine",
    "that girl routine",
    "self improvement",
    "burnout routine",
    "office stress",
    "女生变美",
    "精致生活",
    "提升气质"
]

MIN_LIKE = 5000
MIN_COMMENT = 50

BUY_INTENT_KEYWORDS = [
    "smell", "perfume", "compliment",
    "glow", "routine", "confidence",
    "attractive", "变美", "气质", "精致"
]


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


# ===== 判断是否是“可卖货内容” =====
def is_good_video(v):
    if v["like"] < MIN_LIKE:
        return False

    if v["comment"] < MIN_COMMENT:
        return False

    title = (v["title"] or "").lower()

    for kw in BUY_INTENT_KEYWORDS:
        if kw in title:
            return True

    return False


# ===== 打标签 =====
def tag_video(v):
    title = (v["title"] or "").lower()

    if "burnout" in title or "stress" in title:
        return "打工人情绪"

    if "glow" in title or "变美" in title:
        return "变美动机"

    if "smell" in title or "perfume" in title:
        return "香味吸引"

    if "routine" in title:
        return "生活方式"

    return "其他"


# ===== 给拍摄建议 =====
def generate_angle(tag):
    if tag == "打工人情绪":
        return "👉 可拍：KL打工人 + 奖励自己 + 香味提升状态"

    if tag == "变美动机":
        return "👉 可拍：女生变精致 / 升级感"

    if tag == "香味吸引":
        return "👉 可拍：男生视角 / 被记住的味道"

    if tag == "生活方式":
        return "👉 可拍：routine + 轻带货"

    return "👉 可自由发挥"


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
        print("STATUS:", res.status_code)

        data = res.json()
    except Exception as e:
        print("❌ request error:", e)
        return []

    videos = []

    # ===== 兼容结构 =====
    items = []

    if "data" in data and "videos" in data["data"]:
        items = data["data"]["videos"]

    elif "data" in data and "item_list" in data["data"]:
        items = data["data"]["item_list"]

    elif "aweme_list" in data:
        items = data["aweme_list"]

    else:
        print("❌ unknown structure:", data.keys())
        return []

    for v in items:
        if not isinstance(v, dict):
            continue

        try:
            video_url = v.get("play", "") or v.get("url", "")

            author = ""
            if isinstance(v.get("author"), dict):
                author = v.get("author", {}).get("nickname", "")

            title = v.get("title", "") or v.get("desc", "")

            stats = v.get("stats", {}) or {}

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

    print(f"🎥 found {len(videos)} videos")
    return videos


# ===== 主逻辑 =====
def main():
    all_videos = []

    for k in KEYWORDS:
        vids = search_videos(k)

        for v in vids:
            if is_good_video(v):
                v["tag"] = tag_video(v)
                all_videos.append(v)

        time.sleep(2)

    print(f"🚀 filtered videos: {len(all_videos)}")

    if len(all_videos) == 0:
        send_telegram("❌ 没有筛选到可用的爆款内容（可能API问题或关键词不对）")
        return

    seen = set()

    for v in all_videos:
        if v["url"] in seen:
            continue

        seen.add(v["url"])

        msg = f"""🔥 TikTok选题参考

🏷 标签: {v['tag']}

👤 作者: {v['author']}
📝 标题: {v['title']}

👍 {v['like']} | 💬 {v['comment']}

{generate_angle(v['tag'])}

🔗 {v['url']}
"""

        send_telegram(msg)
        time.sleep(2)

    print("🔥 script finished")


if __name__ == "__main__":
    main()
