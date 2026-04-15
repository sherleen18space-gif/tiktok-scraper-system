print("🔥 script started")

import os, requests, re, time, random
from playwright.sync_api import sync_playwright

# ===== 配置 =====
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE = os.getenv("AIRTABLE_TABLE") or "视频分析"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

KEYWORDS = [
    "skincare",
    "perfume",
    "routine",
    "生活日常",
    "护肤",
    "香水",
    "vlog",
    "morning routine"
]

# ===== 搜索 =====
def search_videos(keyword):
    print(f"🔍 searching: {keyword}")

    url = f"https://www.tiktok.com/search?q={keyword}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(5000)
        except:
            browser.close()
            return []

        links = page.eval_on_selector_all(
            "a[href*='/video/']",
            "els => els.map(e => e.href)"
        )

        browser.close()

    links = list(set(links))
    print(f"🎥 found {len(links)} videos")

    return links[:3]


# ===== 抓数据 =====
def scrape_video(url):
    print(f"📊 scraping: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(4000)
        except:
            browser.close()
            return None

        html = page.content().lower()

        # 数据
        like = re.search(r'"diggcount":(\d+)', html)
        comment = re.search(r'"commentcount":(\d+)', html)

        # 👉 抓标题（比html keyword更准）
        title = re.search(r'<title>(.*?)</title>', html)

        browser.close()

        return {
            "url": url,
            "like": int(like.group(1)) if like else 0,
            "comment": int(comment.group(1)) if comment else 0,
            "title": title.group(1) if title else ""
        }


# ===== 内容判断（核心升级）=====
def is_good_content(data):

    text = data["title"].lower()

    # ✅ 数据层（不要太爆）
    if data["like"] < 1000 or data["comment"] < 20:
        return False

    # ✅ 本地 + 语言
    local_signals = [
        "malaysia", "kl", "my",
        "生活", "日常", "护肤", "推荐", "分享"
    ]

    # ✅ 内容结构
    content_signals = [
        "routine", "review", "vlog",
        "day", "how", "tips", "开箱"
    ]

    if any(s in text for s in local_signals + content_signals):
        return True

    return False


# ===== Airtable =====
def push_airtable(data):
    if not AIRTABLE_API_KEY or not BASE_ID:
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
            "点赞": data["like"],
            "评论": data["comment"]
        }
    }

    requests.post(url, json=payload, headers=headers)


# ===== Telegram =====
def send_telegram(data):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return

    msg = f"""🔥 可参考内容

{data['title']}

{data['url']}

👍 {data['like']}   💬 {data['comment']}
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

    for link in all_links:

        data = scrape_video(link)

        if not data:
            continue

        if not is_good_content(data):
            print("❌ skip")
            continue

        print("✅ GOOD:", data["title"])

        push_airtable(data)
        send_telegram(data)

        time.sleep(random.randint(3,6))

    print("🔥 script finished")


if __name__ == "__main__":
    main()
