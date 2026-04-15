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

# ✅ 扩展关键词（含 Malaysia + perfume）
KEYWORDS = [
    "acne skincare routine",
    "skincare before after",
    "best serum acne",
    "perfume review women",
    "long lasting perfume",
    "perfume recommendation",
    "smell good tips",
    "skincare malaysia",
    "acne malaysia review",
    "perfume malaysia",
    "wangian tahan lama"
]

# ===== 搜索视频（已优化滚动）=====
def search_videos(keyword):
    url = f"https://www.tiktok.com/search?q={keyword}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url)
        page.wait_for_timeout(5000)

        # ✅ 滚动加载更多
        for _ in range(5):
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(2000)

        links = page.eval_on_selector_all(
            "a[href*='/video/']",
            "els => els.map(e => e.href)"
        )

        browser.close()

        return list(set(links))[:30]


# ===== 抓视频数据 =====
def scrape_video(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url)
        page.wait_for_timeout(random.randint(5000,8000))

        html = page.content()

        like = re.search(r'"diggCount":(\d+)', html)
        comment = re.search(r'"commentCount":(\d+)', html)
        play = re.search(r'"playCount":(\d+)', html)

        title = re.search(r'<title>(.*?)</title>', html)

        browser.close()

        return {
            "url": url,
            "like": int(like.group(1)) if like else 0,
            "comment": int(comment.group(1)) if comment else 0,
            "play": int(play.group(1)) if play else 0,
            "title": title.group(1).lower() if title else ""
        }


# ===== 判断是否目标内容（赛道 + 地区）=====
def is_target_content(data):
    text = data["title"]

    keywords = [
        "acne", "skincare", "skin", "serum",
        "cream", "before after",
        "perfume", "fragrance", "smell"
    ]

    malaysia_keywords = [
        "malaysia", "kl", "malay", "wangian"
    ]

    # ✅ 赛道判断
    if any(k in text for k in keywords):
        return True

    # ✅ 地区增强判断（加权）
    if any(k in text for k in malaysia_keywords):
        return True

    return False


# ===== 评分（转化潜力）=====
def evaluate(data):
    score = 0

    if data["like"] > 1000:
        score += 1
    if data["comment"] > 50:
        score += 1
    if data["play"] > 10000:
        score += 1

    if score >= 2:
        return "High"
    elif score == 1:
        return "Medium"
    else:
        return "Low"


# ===== Airtable =====
def push_airtable(data):
    if not AIRTABLE_API_KEY or not BASE_ID:
        print("⚠️ Airtable 未配置")
        return

    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE}"

    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "fields": {
            "视频链接": data["url"],
            "标题": data["title"],
            "点赞数": data["like"],
            "评论数": data["comment"],
            "播放量": data["play"],
            "评级": evaluate(data)
        }
    }

    res = requests.post(url, json=payload, headers=headers)
    print("📡 Airtable:", res.text)


# ===== Telegram =====
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Telegram 未配置")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    res = requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })

    print("📨 Telegram:", res.text)


# ===== 主流程 =====
def main():
    all_links = []

    for k in KEYWORDS:
        print(f"🔍 searching: {k}")
        links = search_videos(k)
        print(f"🎥 found {len(links)} videos")
        all_links += links

    all_links = list(set(all_links))
    print(f"🚀 total videos: {len(all_links)}")

    for link in all_links:
        print(f"\n📊 scraping: {link}")
        data = scrape_video(link)

        print("📊 result:", data)

        # ❌ 非目标内容直接跳过
        if not is_target_content(data):
            print("❌ not related content")
            continue

        # ✅ 全部记录
        push_airtable(data)

        # ✅ 只推高价值
        if evaluate(data) == "High":
            send_telegram(f"🔥可卖视频:\n{link}")

        time.sleep(random.randint(5,10))


# ===== 持续运行（每30分钟）=====
if __name__ == "__main__":
    while True:
        main()
        print("\n⏳ 等待30分钟...\n")
        time.sleep(1800)
