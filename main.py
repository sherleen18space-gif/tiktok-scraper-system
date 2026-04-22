print("🔥 script started")

import os
import requests
import time
import json

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

# ⬇️ TURUNKAN dulu untuk debug — nanti boleh naikkan balik
MIN_LIKE = 500
MIN_COMMENT = 10

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
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        print(f"📨 Telegram: {r.status_code}")
    except Exception as e:
        print("❌ telegram error:", e)


# ===== Debug: Print raw response =====
def debug_print_structure(data, keyword):
    """Cetak structure API response untuk kita faham format sebenar"""
    print(f"\n===== DEBUG: '{keyword}' =====")
    print(f"Top-level keys: {list(data.keys())}")

    if "data" in data:
        d = data["data"]
        if isinstance(d, dict):
            print(f"data keys: {list(d.keys())}")

            # Cuba tengok 1 item je
            for k in ["videos", "item_list", "aweme_list", "items"]:
                if k in d and isinstance(d[k], list) and len(d[k]) > 0:
                    print(f"First item keys in data['{k}']: {list(d[k][0].keys())}")
                    # Tengok stats field
                    first = d[k][0]
                    for stats_key in ["stats", "statistics", "aweme_statistics"]:
                        if stats_key in first:
                            print(f"Stats keys: {list(first[stats_key].keys())}")
                    break

    # Save raw response untuk tengok bila ada masa
    try:
        with open(f"debug_{keyword[:10].replace(' ', '_')}.json", "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved debug JSON")
    except:
        pass

    print("=" * 40)


# ===== Extract stats dengan multi-key fallback =====
def extract_stats(v):
    """Cuba semua kemungkinan key untuk like & comment"""
    like = 0
    comment = 0

    # Cuba dari stats / statistics
    for stats_key in ["stats", "statistics", "aweme_statistics"]:
        s = v.get(stats_key, {})
        if isinstance(s, dict) and s:
            like = s.get("diggCount") or s.get("like_count") or s.get("playCount") or 0
            comment = s.get("commentCount") or s.get("comment_count") or 0
            if like > 0:
                break

    # Fallback: terus dalam v
    if like == 0:
        like = v.get("diggCount") or v.get("like_count") or v.get("likes") or 0

    if comment == 0:
        comment = v.get("commentCount") or v.get("comment_count") or v.get("comments") or 0

    return int(like), int(comment)


# ===== Extract video URL dengan fallback =====
def extract_url(v):
    for key in ["play", "url", "video_url", "share_url", "webVideoUrl"]:
        val = v.get(key)
        if val and isinstance(val, str) and val.startswith("http"):
            return val

    # Nested dalam video dict
    video = v.get("video", {})
    if isinstance(video, dict):
        for key in ["play_addr", "play", "url"]:
            val = video.get(key)
            if isinstance(val, dict):
                val = val.get("url_list", [None])[0]
            if val and isinstance(val, str) and val.startswith("http"):
                return val

    return ""


# =====判断是否是"可卖货内容" =====
def is_good_video(v):
    if v["like"] < MIN_LIKE:
        return False

    if v["comment"] < MIN_COMMENT:
        return False

    title = (v["title"] or "").lower()

    # Kalau title kosong, still accept berdasarkan engagement je
    if not title:
        return True

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
    angles = {
        "打工人情绪": "👉 可拍：KL打工人 + 奖励自己 + 香味提升状态",
        "变美动机": "👉 可拍：女生变精致 / 升级感",
        "香味吸引": "👉 可拍：男生视角 / 被记住的味道",
        "生活方式": "👉 可拍：routine + 轻带货",
    }
    return angles.get(tag, "👉 可自由发挥")


# ===== 抓数据 =====
def search_videos(keyword, debug=False):
    print(f"\n🔍 searching: {keyword}")

    url = "https://tiktok-scraper7.p.rapidapi.com/feed/search"

    querystring = {
        "keywords": keyword,
        "count": "10",        # Naikkan dari 5 → 10
        "cursor": "0",
        "region": "MY",
        "publish_time": "0"   # 0 = semua masa, 1 = 24j, 7 = seminggu
    }

    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
    }

    try:
        res = requests.get(url, headers=headers, params=querystring, timeout=30)
        print(f"📡 Status: {res.status_code}")

        if res.status_code != 200:
            print(f"❌ Non-200: {res.text[:300]}")
            return []

        data = res.json()

    except Exception as e:
        print("❌ request error:", e)
        return []

    # Debug structure (first keyword je)
    if debug:
        debug_print_structure(data, keyword)

    videos = []

    # ===== Multi-path structure parsing =====
    items = []

    if "data" in data:
        d = data["data"]
        if isinstance(d, dict):
            for k in ["videos", "item_list", "aweme_list", "items"]:
                if k in d and isinstance(d[k], list):
                    items = d[k]
                    print(f"✅ Found {len(items)} items via data['{k}']")
                    break
        elif isinstance(d, list):
            items = d
            print(f"✅ data is direct list: {len(items)} items")

    elif "aweme_list" in data:
        items = data["aweme_list"]
        print(f"✅ Found {len(items)} items via aweme_list")

    elif "item_list" in data:
        items = data["item_list"]
        print(f"✅ Found {len(items)} items via item_list")

    else:
        print(f"❌ Unknown structure. Keys: {list(data.keys())}")
        return []

    for v in items:
        if not isinstance(v, dict):
            continue

        try:
            video_url = extract_url(v)

            author = ""
            a = v.get("author", {})
            if isinstance(a, dict):
                author = a.get("nickname") or a.get("unique_id") or ""
            elif isinstance(a, str):
                author = a

            title = v.get("title") or v.get("desc") or v.get("text") or ""

            like, comment = extract_stats(v)

            print(f"  📹 {title[:40]!r} | 👍{like} 💬{comment} | url={'✅' if video_url else '❌'}")

            videos.append({
                "url": video_url,
                "author": author,
                "title": title,
                "like": like,
                "comment": comment
            })

        except Exception as e:
            print("⚠️ skip one:", e)

    print(f"🎥 Parsed {len(videos)} videos from '{keyword}'")
    return videos


# ===== 主逻辑 =====
def main():
    all_videos = []
    first_keyword = True

    for k in KEYWORDS:
        # Debug mode untuk keyword pertama je
        vids = search_videos(k, debug=first_keyword)
        first_keyword = False

        print(f"  Before filter: {len(vids)} | After filter: ", end="")
        filtered = [v for v in vids if is_good_video(v)]
        print(len(filtered))

        for v in filtered:
            v["tag"] = tag_video(v)
            all_videos.append(v)

        time.sleep(2)

    print(f"\n🚀 Total filtered videos: {len(all_videos)}")

    if len(all_videos) == 0:
        msg = (
            "❌ Tiada video lepas filter\n"
            f"MIN_LIKE={MIN_LIKE} | MIN_COMMENT={MIN_COMMENT}\n"
            "Cuba turunkan threshold atau semak API key"
        )
        send_telegram(msg)
        return

    seen = set()

    for v in all_videos:
        url_key = v["url"] or v["title"]  # fallback dedup by title
        if url_key in seen:
            continue

        seen.add(url_key)

        msg = f"""🔥 TikTok选题参考

🏷 标签: {v['tag']}
👤 作者: {v['author']}
📝 标题: {v['title']}

👍 {v['like']} | 💬 {v['comment']}

{generate_angle(v['tag'])}

🔗 {v['url'] or '(no url)'}
"""
        send_telegram(msg)
        time.sleep(2)

    print("✅ script finished")


if __name__ == "__main__":
    main()
