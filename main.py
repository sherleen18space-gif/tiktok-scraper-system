print("🔥 script started")

import os
import requests
import re
import time
import random
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

# ===== 配置 =====
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE = os.getenv("AIRTABLE_TABLE") or "视频分析"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== 关键词（生活 + 产品 + 本地）=====
KEYWORDS = [
    "skincare",
    "acne",
    "perfume",
    "selfcare",
    "glowup",
    "thatgirl",
    "cleangirl",
    "morning routine",
    "night routine",
    "生活日常",
    "护肤分享",
    "香水推荐"
]

# ===== 搜索视频 =====
def search_videos(keyword):
    print(f"🔍 searching: {keyword}")

    tag = keyword.replace(" ", "")
    url = f"https://www.tiktok.com/tag/{tag}"

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)",
            viewport={"width": 390, "height": 844},
            locale="en-US"
        )

        page = context.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(8000)
        except:
            print("❌ load failed")
            browser.close()
            return []

        links = page.eval_on_selector_all(
            "a[href*='/video/']",
            "els => els.map(e => e.href)"
        )

        browser.close()

        links = list(set(links))[:3]  # 每关键词3个
        print(f"🎥 found {len(links)} videos")

        return links


# ===== 抓视频数据 =====
def scrape_video(url):
    print(f"📊 scraping: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"
        )

        page = context.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(random.randint(4000,7000))
        except:
            browser.close()
            return None

        html = page.content().lower()
        browser.close()

    # ===== 数据提取 =====
    like = re.search(r'"diggcount":(\d+)', html)
    comment = re.search(r'"commentcount":(\d+)', html)
    play = re.search(r'"playcount":(\d+)', html)

    caption = re.search(r'"desc":"(.*?)"', html)
    author = re.search(r'"author":"(.*?)"', html)
    create_time = re.search(r'"createtime":(\d+)', html)

    return {
        "url": url,
        "like": int(like.group(1)) if like else 0,
        "comment": int(comment.group(1)) if comment else 0,
        "play": int(play.group(1)) if play else 0,
        "caption": caption.group(1) if caption else "",
        "author": author.group(1) if author else "",
        "time": int(create_time.group(1)) if create_time else 0,
        "html": html
    }


# ===== 内容过滤 =====
def is_content(data):
    text = (data["caption"] + data["html"]).lower()

    good = [
        "routine", "how to", "tips", "habits",
        "glow up", "self care", "day in my life",
        "skincare", "perfume", "review"
    ]

    bad = [
        "cat", "dog", "funny", "meme",
        "prank", "challenge"
    ]

    if any(b in text for b in bad):
        return False

    if not any(g in text for g in good):
        return False

    return True


# ===== 时间过滤 =====
def is_recent(data):
    if data["time"] == 0:
        return True

    video_time = datetime.fromtimestamp(data["time"])
    return datetime.now() - video_time < timedelta(days=14)


# ===== 地区过滤 =====
def is_local(data):
    text = (data["caption"] + data["author"]).lower()

    asia = [
        "malaysia", "kuala lumpur", "malay",
        "singapore", "sg", "indonesia", "thai"
    ]

    return any(a in text for a in asia)


# ===== Airtable =====
def push_airtable(data):
    if not AIRTABLE_API_KEY or not BASE_ID:
        print("⚠️ Airtable skipped")
        return

    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE}"

    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "fields": {
            "Author": data["author"],
            "Caption": data["caption"],
            "URL": data["url"],
            "Like": data["like"],
            "Comment": data["comment"],
            "Play": data["play"]
        }
    }

    r = requests.post(url, json=payload, headers=headers)
    print("📡 Airtable:", r.text)


# ===== Telegram =====
def send_telegram(data):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Telegram skipped")
        return

    msg = f"""🔥 内容参考

👤 {data['author']}
👍 {data['like']} 💬 {data['comment']}

📝 {data['caption'][:80]}

🔗 {data['url']}
"""

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })


# ===== 主流程 =====
def main():
    all_links = []

    for k in KEYWORDS:
        all_links += search_videos(k)

    all_links = list(set(all_links))
    print(f"🚀 total videos: {len(all_links)}")

    if len(all_links) == 0:
        print("❌ no videos found")
        return

    for link in all_links:
        data = scrape_video(link)

        if not data:
            continue

        if not is_content(data):
            print("❌ not content")
            continue

        if not is_recent(data):
            print("⏰ too old")
            continue

        if not is_local(data):
            print("🌍 not local")
            continue

        print("✅ good video")

        push_airtable(data)
        send_telegram(data)

        time.sleep(random.randint(5,10))

    print("🔥 script finished")


if __name__ == "__main__":
    main()
