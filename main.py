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
TABLE = "视频分析"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 🎯 你的目标赛道（已加 perfume）
TARGET_KEYWORDS = [
    "acne", "skincare", "pimple",
    "stress", "anxiety",
    "perfume", "fragrance", "scent"
]

# 💰 购买意图关键词
BUY_KEYWORDS = [
    "where to buy", "link please", "how much",
    "need this", "want this",
    "多少钱", "哪里买", "想要"
]

# 🎬 广告hook词
HOOK_WORDS = [
    "you won't believe",
    "this changed my life",
    "before after",
    "stop doing this",
    "doctor said"
]

# ===== 抓推荐视频 =====
def get_trending_videos():
    print("🔍 grabbing trending videos")
    links = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("https://www.tiktok.com/")
        page.wait_for_timeout(5000)

        for _ in range(5):
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

# ===== 抓视频数据 =====
def scrape_video(url):
    print(f"📊 scraping: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url)
        page.wait_for_timeout(random.randint(4000, 7000))

        html = page.content()

        like = re.search(r'"diggCount":(\d+)', html)
        comment = re.search(r'"commentCount":(\d+)', html)
        play = re.search(r'"playCount":(\d+)', html)

        browser.close()

        data = {
            "url": url,
            "like": int(like.group(1)) if like else 0,
            "comment": int(comment.group(1)) if comment else 0,
            "play": int(play.group(1)) if play else 0,
            "html": html.lower()
        }

        print("📊 result:", data)

        return data

# ===== 是否目标人群 =====
def is_target(html):
    return any(k in html for k in TARGET_KEYWORDS)

# ===== 评分系统（核心） =====
def evaluate(data):
    html = data["html"]
    score = 0

    # 基础数据
    if data["like"] > 1000:
        score += 1
    if data["comment"] > 50:
        score += 1

    # 🔥 购买意图
    for kw in BUY_KEYWORDS:
        if kw in html:
            score += 5

    # 🎬 广告潜力
    for kw in HOOK_WORDS:
        if kw in html:
            score += 2

    if score >= 6:
        return "High"
    elif score >= 3:
        return "Medium"
    else:
        return "Low"

# ===== Airtable =====
def push_airtable(data, level):
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
            "购买意图": level
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

        # 🎯 过滤目标内容
        if not is_target(data["html"]):
            print("❌ not target audience")
            continue

        level = evaluate(data)

        push_airtable(data, level)

        if level == "High":
            send_telegram(f"🔥可卖视频 ({level})\n{link}")

        time.sleep(random.randint(5, 10))

    print("🔥 script finished")

if __name__ == "__main__":
    main()
