import os
from playwright.sync_api import sync_playwright
import requests, re, time, random

# ===== 配置 =====
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID") 
TABLE = "视频分析"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

KEYWORDS = ["acne skincare", "stress relief"]

# ===== 抓搜索结果 =====
def search_videos(keyword):
    url = f"https://www.tiktok.com/search?q={keyword}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(5000)

        links = page.eval_on_selector_all(
            "a[href*='/video/']",
            "els => els.map(e => e.href)"
        )

        browser.close()
        return list(set(links))[:5]

# ===== 抓数据 =====
def scrape_video(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_timeout(random.randint(3000,6000))

        html = page.content()

        like = re.search(r'"diggCount":(\d+)', html)
        comment = re.search(r'"commentCount":(\d+)', html)
        play = re.search(r'"playCount":(\d+)', html)

        browser.close()

        return {
            "url": url,
            "like": int(like.group(1)) if like else 0,
            "comment": int(comment.group(1)) if comment else 0,
            "play": int(play.group(1)) if play else 0
        }

# ===== 判断购买意图 =====
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

    requests.post(url, json=payload, headers=headers)

# ===== Telegram 通知 =====
def send_telegram(msg):
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

    for link in all_links:
        data = scrape_video(link)
        push_airtable(data)

        if evaluate(data) == "High":
            send_telegram(f"🔥可卖视频:\n{link}")

        time.sleep(random.randint(5,10))

if __name__ == "__main__":
    main()
