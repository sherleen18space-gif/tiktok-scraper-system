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
    "car fragrance",
    "car smell good",
    "女生变美",
    "精致生活",
    "提升气质",
    "车内香氛",
    "男生日常"
]

# 过滤门槛（可调整）
MIN_LIKE = 10000
MIN_COMMENT = 100

BUY_INTENT_KEYWORDS = [
    "smell", "perfume", "fragrance", "compliment", "scent",
    "glow", "routine", "confidence", "attractive",
    "car", "drive", "dashboard",
    "变美", "气质", "精致", "香氛", "香味", "男生"
]


# ===== Telegram =====
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Telegram 配置缺失")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        r = requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        })
        print(f"📨 Telegram 发送: {r.status_code}")
    except Exception as e:
        print("❌ Telegram 错误:", e)


# ===== 提取 like / comment（修复 snake_case）=====
def extract_stats(v):
    # 这个 API 直接放在顶层，用 snake_case
    like = (
        v.get("digg_count") or
        v.get("diggCount") or
        v.get("like_count") or
        v.get("likes") or
        0
    )

    comment = (
        v.get("comment_count") or
        v.get("commentCount") or
        v.get("comments") or
        0
    )

    # 备用：从 stats / statistics 嵌套里找
    if like == 0:
        for stats_key in ["stats", "statistics", "aweme_statistics"]:
            s = v.get(stats_key, {})
            if isinstance(s, dict) and s:
                like = (
                    s.get("digg_count") or
                    s.get("diggCount") or
                    s.get("like_count") or
                    0
                )
                comment = (
                    s.get("comment_count") or
                    s.get("commentCount") or
                    0
                )
                if like > 0:
                    break

    return int(like), int(comment)


# ===== 提取视频链接（多路径兼容）=====
def extract_url(v):
    for key in ["play", "url", "video_url", "share_url", "webVideoUrl"]:
        val = v.get(key)
        if val and isinstance(val, str) and val.startswith("http"):
            return val

    video = v.get("video", {})
    if isinstance(video, dict):
        for key in ["play_addr", "play", "url"]:
            val = video.get(key)
            if isinstance(val, dict):
                val = val.get("url_list", [None])[0]
            if val and isinstance(val, str) and val.startswith("http"):
                return val

    return ""


# ===== 判断是否值得参考 =====
def is_good_video(v):
    if v["like"] < MIN_LIKE:
        return False
    if v["comment"] < MIN_COMMENT:
        return False

    title = (v["title"] or "").lower()

    # 标题为空也接受（高互动就够了）
    if not title:
        return True

    for kw in BUY_INTENT_KEYWORDS:
        if kw in title:
            return True

    return False


# ===== 打标签 =====
def tag_video(v):
    title = (v["title"] or "").lower()

    if any(k in title for k in ["car", "drive", "dashboard", "车", "香氛"]):
        return "🚗 车内香氛"
    if any(k in title for k in ["burnout", "stress", "office", "work", "打工"]):
        return "💼 打工人情绪"
    if any(k in title for k in ["glow", "变美", "beauty", "transform"]):
        return "✨ 变美动机"
    if any(k in title for k in ["smell", "perfume", "fragrance", "scent", "香味"]):
        return "🌸 香味吸引"
    if any(k in title for k in ["routine", "精致", "lifestyle", "日常"]):
        return "🌿 生活方式"
    if any(k in title for k in ["confidence", "man", "男", "masculine"]):
        return "💪 男士魅力"

    return "📌 其他"


# ===== 拍摄建议 =====
def generate_angle(tag):
    angles = {
        "🚗 车内香氛":   "👉 拍角度：开车时挂香氛 + 女生坐进来闻到 + 被记住的味道",
        "💼 打工人情绪": "👉 拍角度：KL打工人下班奖励自己 + 香味提升状态 + 开车回家放松",
        "✨ 变美动机":   "👉 拍角度：升级感 / 精致男生日常 + 车内细节",
        "🌸 香味吸引":   "👉 拍角度：男生视角 / 车里被记住的味道 / 约会前必备",
        "🌿 生活方式":   "👉 拍角度：routine vlog + 车香轻带货",
        "💪 男士魅力":   "👉 拍角度：自信男生日常 + 香味加分 + 软性带货",
    }
    return angles.get(tag, "👉 可自由发挥，结合车香产品自然植入")


# ===== 数字格式化 =====
def fmt_num(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


# ===== 搜索视频 =====
def search_videos(keyword, debug=False):
    print(f"\n🔍 搜索中: {keyword}")

    url = "https://tiktok-scraper7.p.rapidapi.com/feed/search"

    params = {
        "keywords": keyword,
        "count": "10",
        "cursor": "0",
        "region": "MY",
        "publish_time": "0"
    }

    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "tiktok-scraper7.p.rapidapi.com"
    }

    try:
        res = requests.get(url, headers=headers, params=params, timeout=30)
        print(f"📡 状态码: {res.status_code}")

        if res.status_code != 200:
            print(f"❌ 非200响应: {res.text[:300]}")
            return []

        data = res.json()

    except Exception as e:
        print("❌ 请求错误:", e)
        return []

    # Debug 模式保存原始 JSON
    if debug:
        try:
            fname = f"debug_{keyword[:15].replace(' ', '_')}.json"
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 已保存: {fname}")
        except:
            pass

    # 解析 items
    items = []

    if "data" in data:
        d = data["data"]
        if isinstance(d, dict):
            for k in ["videos", "item_list", "aweme_list", "items"]:
                if k in d and isinstance(d[k], list):
                    items = d[k]
                    break
        elif isinstance(d, list):
            items = d
    elif "aweme_list" in data:
        items = data["aweme_list"]
    elif "item_list" in data:
        items = data["item_list"]
    else:
        print(f"❌ 未知结构，顶层 keys: {list(data.keys())}")
        return []

    videos = []

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

            title = v.get("title") or v.get("desc") or v.get("content_desc") or ""
            like, comment = extract_stats(v)

            print(f"  {'✅' if like >= MIN_LIKE else '➖'} 👍{fmt_num(like)} 💬{fmt_num(comment)} | {title[:45]!r}")

            videos.append({
                "url": video_url,
                "author": author,
                "title": title,
                "like": like,
                "comment": comment
            })

        except Exception as e:
            print("⚠️ 跳过一条:", e)

    print(f"🎥 共解析 {len(videos)} 条 | 关键词: {keyword}")
    return videos


# ===== 主逻辑 =====
def main():
    all_videos = []
    first = True

    for k in KEYWORDS:
        vids = search_videos(k, debug=first)
        first = False

        filtered = [v for v in vids if is_good_video(v)]
        print(f"  过滤前: {len(vids)} | 过滤后: {len(filtered)}")

        for v in filtered:
            v["tag"] = tag_video(v)
            all_videos.append(v)

        time.sleep(2)

    print(f"\n🚀 最终爆款视频数量: {len(all_videos)}")

    # ===== 没有结果时的诊断报告 =====
    if len(all_videos) == 0:
        msg = (
            "❌ <b>今日无爆款内容</b>\n\n"
            f"过滤门槛：👍 {fmt_num(MIN_LIKE)} | 💬 {MIN_COMMENT}\n"
            f"搜索关键词数：{len(KEYWORDS)} 个\n\n"
            "可能原因：\n"
            "• API 今日限额用完\n"
            "• 门槛设太高\n"
            "• 关键词需要更新\n\n"
            "👉 建议：调低 MIN_LIKE 或更换关键词"
        )
        send_telegram(msg)
        return

    # ===== 发送汇总头部 =====
    send_telegram(
        f"🔥 <b>今日 TikTok 爆款选题</b>\n\n"
        f"共找到 <b>{len(all_videos)}</b> 条参考视频\n"
        f"标准：👍 ≥{fmt_num(MIN_LIKE)} | 💬 ≥{MIN_COMMENT}\n"
        f"━━━━━━━━━━━━━━━"
    )

    time.sleep(1)

    # ===== 逐条发送 =====
    seen = set()

    for v in all_videos:
        dedup_key = v["url"] or v["title"]
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        tag = v["tag"]
        msg = (
            f"{tag}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 <b>{v['author']}</b>\n"
            f"📝 {v['title']}\n\n"
            f"👍 {fmt_num(v['like'])}  💬 {fmt_num(v['comment'])}\n\n"
            f"{generate_angle(tag)}\n\n"
            f"🔗 {v['url'] or '(无链接)'}"
        )

        send_telegram(msg)
        time.sleep(2)

    # ===== 结尾总结 =====
    send_telegram("✅ <b>今日选题推送完毕，开拍吧！🎬</b>")
    print("✅ 脚本运行完成")


if __name__ == "__main__":
    main()
