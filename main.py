print("🔥 script started")

import os
import requests
import re
import time
import random
from playwright.sync_api import sync_playwright

# ===== 配置 =====
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE = os.getenv("AIRTABLE_TABLE") or "视频分析"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

KEYWORDS = [
    "skincare routine",
    "acne tips",
    "perfume girl",
    "how to smell good",
    "that girl routine",
    "self care day",
    "glow up tips",
    "morning routine girl",
    "clean girl lifestyle"
]

# ===== 搜索视频 =====
def search_videos(keyword):
    print(f"🔍 searching: {keyword}")

    url = f"https://www.tiktok.com/search?q={keyword}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"
        )

        page = context.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_selector("a[href*='/video/']", timeout=15000)
        except:
            print("❌ load failed")
            browser.close()
            return []

        links = page.eval_on_selector_all(
            "a[href*='/video/']",
            "els => els.map(e => e.href)"
        )

        browser.close()

        links = list(set(links))
        print(f"🎥 found {len(links)} videos")

        return links[:5]


# ===== 抓数据 =====
def scrape_video(url):
    print(f"📊 scraping: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

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

        like = re.search(r'"diggcount":(\d+)', html)
        comment = re.search(r'"commentcount":(\d+)', html)
        play = re.search(r'"playcount":(\d+)', html)

        browser.close()

        return {
            "url": url,
            "like": int(like.group(1)) if like else 0,
            "comment": int(comment.group(1)) if comment else 0,
            "play": int(play.group(1)) if play else 0,
            "html": html
        }


# ===== 判断内容类型 =====
def is_good_content(data):
    text = data["html"]

    signals = [
        "routine",
        "how to",
        "tips",
        "habits",
        "glow up",
        "self care",
        "day in my life"
    ]

    return any(s in text for s in signals)


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
            "视频链接": data["url"],
            "点赞": data["like"],
            "评论": data["comment"],
            "播放": data["play"]
        }
    }

    r = requests.post(url, json=payload, headers=headers)
    print("📡 Airtable:", r.text)


# ===== Telegram =====
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Telegram skipped")
        return

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

    # fallback（保证一定有数据）
    if len(all_links) == 0:
        print("⚠️ using fallback")
        all_links = [
            "https://www.tiktok.com/tag/skincare",
            "https://www.tiktok.com/tag/glowup"
        ]

    for link in all_links:
        data = scrape_video(link)

        if not data:
            continue

        if not is_good_content(data):
            print("❌ skip non-content")
            continue

        push_airtable(data)

        send_telegram(
            f"🔥 内容参考\n\n{data['url']}\n👍 {data['like']} 💬 {data['comment']}"
        )

        time.sleep(random.randint(5,10))

    print("🔥 script finished")


if __name__ == "__main__":
    main()
