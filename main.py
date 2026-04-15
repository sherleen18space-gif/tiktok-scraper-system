print("🔥 script started")

import os
import requests, re, time, random
from playwright.sync_api import sync_playwright

# ===== 配置 =====
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID") 
TABLE = os.getenv("AIRTABLE_TABLE")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 👉 关键词只用于分类，不再用于搜索
KEYWORDS = ["beauty", "stress", "healing"]

# ===== 抓 TikTok 推荐视频 =====
def get_trending_videos():
    print("🔍 grabbing trending videos")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled"
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15"
        )

        page = context.new_page()

        page.goto("https://www.tiktok.com/", timeout=60000)

        # 👇 等加载
        page.wait_for_timeout(8000)

        # 👇 模拟用户滑动（关键）
        for _ in range(3):
            page.mouse.wheel(0, random.randint(2000, 4000))
            page.wait_for_timeout(random.randint(2000, 4000))

        links = page.eval_on_selector_all(
            "a[href*='/video/']",
            "els => els.map(e => e.href)"
        )

        browser.close()

        links = list(set(links))
        print(f"🎥 found {len(links)} videos")

        return links[:8]


# ===== 抓视频数据 =====
def scrape_video(url):
    print(f"📊 scraping: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

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


# ===== 判断赚钱潜力 =====
def evaluate(data):
    if data["comment"] > 100 and data["like"] > 1000:
        return "High"
    elif data["comment"] > 30:
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

        # 👉 避免垃圾数据
        if data["play"] == 0:
            print("⚠️ skip empty")
            continue

        push_airtable(data)

        result = evaluate(data)

        if result == "High":
            send_telegram(f"🔥可卖视频:\n{link}")

        time.sleep(random.randint(5,10))

    print("🔥 script finished")


if __name__ == "__main__":
    main()
