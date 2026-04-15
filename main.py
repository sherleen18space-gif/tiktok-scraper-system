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

KEYWORDS = [
    "acne skincare routine",
    "skincare before after",
    "perfume review",
    "perfume malaysia",
    "skincare malaysia",
    "glow up skin",
    "smell good tips"
]

# ===== 搜索视频 =====
def search_videos(keyword):
    print(f"🔍 searching: {keyword}")

    url = f"https://www.tiktok.com/search?q={keyword}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        page = context.new_page()

        # 🚀 阻止图片/视频 加速
        page.route("**/*", lambda route: route.abort()
            if route.request.resource_type in ["image","media","font"]
            else route.continue_())

        try:
            page.goto(url, timeout=30000)
            page.wait_for_timeout(5000)

            for _ in range(5):
                page.mouse.wheel(0, 3000)
                page.wait_for_timeout(2000)

            links = page.eval_on_selector_all(
                "a[href*='/video/']",
                "els => els.map(e => e.href)"
            )

            print(f"🎥 found {len(links)}")

        except Exception as e:
            print("❌ error:", e)
            links = []

        browser.close()
        return list(set(links))[:20]


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


# ===== 内容分类 =====
def classify_content(data):
    text = data["title"]

    if any(x in text for x in ["before", "after", "transformation"]):
        return "Transformation"

    if any(x in text for x in ["routine", "daily", "skincare"]):
        return "Routine"

    if any(x in text for x in ["review", "honest", "try"]):
        return "Review"

    if any(x in text for x in ["relax", "satisfying"]):
        return "Satisfying"

    if any(x in text for x in ["perfume", "fragrance", "smell"]):
        return "Perfume"

    return "Other"


# ===== 涨粉潜力判断 =====
def is_follow_potential(data):
    text = data["title"]

    keywords = [
        "i tried", "day 1", "day 7",
        "results", "this changed",
        "people ask me", "glow up"
    ]

    return any(k in text for k in keywords)


# ===== Airtable =====
def push_airtable(data, content_type, follow):
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
            "内容类型": content_type,
            "涨粉潜力": follow
        }
    }

    res = requests.post(url, json=payload, headers=headers)
    print("📡 Airtable:", res.text)


# ===== Telegram =====
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
    print(f"🚀 total: {len(all_links)}")

    for link in all_links:
        print(f"\n📊 {link}")
        data = scrape_video(link)

        content_type = classify_content(data)
        follow = is_follow_potential(data)

        print("📊 类型:", content_type)
        print("📊 涨粉:", follow)

        push_airtable(data, content_type, follow)

        if follow:
            send_telegram(f"🔥涨粉视频\n类型:{content_type}\n{link}")

        time.sleep(random.randint(5,10))


# ===== 持续运行 =====
if __name__ == "__main__":
    while True:
        main()
        print("⏳ 30分钟后再跑...")
        time.sleep(1800)
