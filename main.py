print("🔥 script started")

import os
import requests, re, time, random
from playwright.sync_api import sync_playwright

# ===== 配置（从 GitHub Secrets 读取）=====
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID") 
TABLE = os.getenv("AIRTABLE_TABLE")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

KEYWORDS = ["acne skincare", "stress relief"]

# ===== 检查环境变量 =====
print("AIRTABLE_API_KEY:", "OK" if AIRTABLE_API_KEY else "❌ missing")
print("BASE_ID:", BASE_ID)
print("TABLE:", TABLE)
print("TELEGRAM_TOKEN:", "OK" if TELEGRAM_TOKEN else "❌ missing")
print("CHAT_ID:", CHAT_ID)


# ===== 抓 TikTok 搜索 =====
def search_videos(keyword):
    url = f"https://www.tiktok.com/search?q={keyword}"
    print(f"🔍 searching: {keyword}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        page.goto(url, timeout=60000)
        page.wait_for_timeout(8000)

        links = page.eval_on_selector_all(
            "a[href*='/video/']",
            "els => els.map(e => e.href)"
        )

        browser.close()

        links = list(set(links))
        print(f"🎥 found {len(links)} videos")

        return links[:5]


# ===== 抓视频数据 =====
def scrape_video(url):
    print(f"📊 scraping: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        page.goto(url, timeout=60000)
        page.wait_for_timeout(random.randint(5000,8000))

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


# ===== 判断是否值得卖 =====
def evaluate(data):
    if data["comment"] > 50 and data["like"] > 500:
        return "High"
    elif data["comment"] > 20:
        return "Medium"
    else:
        return "Low"


# ===== 写入 Airtable =====
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
    print("📡 Airtable response:", res.text)


# ===== Telegram =====
def send_telegram(msg):
    print("📨 sending telegram")

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    res = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

    print("📨 Telegram response:", res.text)


# ===== 主流程 =====
def main():
    all_links = []

    for k in KEYWORDS:
        all_links += search_videos(k)

    all_links = list(set(all_links))

    print(f"🚀 total videos: {len(all_links)}")

    for link in all_links:
        data = scrape_video(link)

        if data["play"] == 0:
            print("⚠️ skip empty data")
            continue

        push_airtable(data)

        result = evaluate(data)

        if result == "High":
            send_telegram(f"🔥可卖视频:\n{link}")

        time.sleep(random.randint(5,10))

    print("🔥 script finished")


if __name__ == "__main__":
    main()
