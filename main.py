print("🔥 script started")

import os
from playwright.sync_api import sync_playwright
import requests, re, time, random

# ===== 配置 =====
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE = "视频分析"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ✅ 先用固定视频（测试用）
TEST_LINKS = [
    "https://www.tiktok.com/@scout2015/video/6718335390845095173"
]

# ===== 抓数据 =====
def scrape_video(url):
    print(f"📥 scraping: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        page = browser.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(random.randint(4000,6000))

            html = page.content()

            like = re.search(r'"diggCount":(\d+)', html)
            comment = re.search(r'"commentCount":(\d+)', html)
            play = re.search(r'"playCount":(\d+)', html)

            data = {
                "url": url,
                "like": int(like.group(1)) if like else 0,
                "comment": int(comment.group(1)) if comment else 0,
                "play": int(play.group(1)) if play else 0
            }

            print("✅ scraped:", data)
            return data

        except Exception as e:
            print("❌ scrape error:", e)
            return None

        finally:
            browser.close()


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
    print("📤 pushing to Airtable")

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
    print("Airtable response:", res.text)


# ===== Telegram 通知 =====
def send_telegram(msg):
    print("📨 sending telegram")

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    res = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

    print("Telegram response:", res.text)


# ===== 主流程 =====
def main():
    print("🚀 main started")

    all_links = TEST_LINKS   # ❗先用测试

    for link in all_links:
        data = scrape_video(link)

        if not data:
            continue

        push_airtable(data)

        result = evaluate(data)
        print("📊 result:", result)

        if result == "High":
            send_telegram(f"🔥可卖视频:\n{link}")

        time.sleep(5)

    print("🔥 script finished")


if __name__ == "__main__":
    main()
