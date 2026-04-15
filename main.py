print("🔥 script started")

import os
import requests
import re
import time
import random
from playwright.sync_api import sync_playwright

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE = "视频分析"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ===== 抓推荐流 =====
def get_trending_videos():
    print("🔍 grabbing trending videos")

    links = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://www.tiktok.com/")

        # 模拟用户刷视频
        for i in range(5):
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(3000)

            new_links = page.eval_on_selector_all(
                "a[href*='/video/']",
                "els => els.map(e => e.href)"
            )

            links += new_links

        browser.close()

    links = list(set(links))
    print(f"🎥 found {len(links)} videos")

    return links[:10]

# ===== 抓数据 =====
def scrape_video(url):
    print(f"📊 scraping: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url)
        page.wait_for_timeout(5000)

        html = page.content()

        like = re.search(r'"diggCount":(\d+)', html)
        comment = re.search(r'"commentCount":(\d+)', html)
        play = re.search(r'"playCount":(\d+)', html)

        browser.close()

        data = {
            "url": url,
            "like": int(like.group(1)) if like else 0,
            "comment": int(comment.group(1)) if comment else 0,
            "play": int(play.group(1)) if play else 0
        }

        print("📊 result:", data)

        return data

# ===== 判断 =====
def evaluate(data):
    if data["comment"] > 50 and data["like"] > 500:
        return "High"
    elif data["comment"] > 20:
        return "Medium"
    else:
        return "Low"

# ===== Airtable =====
def push_airtable(data):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE}"

    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "fields": {
            "视频链接": data["url"],
            "点赞数": data["like"],
            "评论数": data["comment"],
            "播放量": data["play"],
            "购买意图": evaluate(data)
        }
    }

    res = requests.post(url, json=payload, headers=headers)
    print("📡 Airtable:", res.text)

# ===== Telegram =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    res = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

    print("📨 Telegram:", res.text)

# ===== 主流程 =====
def main():
    links = get_trending_videos()

    if not links:
        print("❌ no videos found")
        return

    for link in links:
        data = scrape_video(link)

        push_airtable(data)

        if evaluate(data) == "High":
            send_telegram(f"🔥可卖视频:\n{link}")

        time.sleep(random.randint(5, 10))

    print("🔥 script finished")

if __name__ == "__main__":
    main()
