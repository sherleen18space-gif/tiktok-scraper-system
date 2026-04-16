print("🔥 script started")

import os, requests, re, time, random
from playwright.sync_api import sync_playwright

# ===== 配置 =====
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE = os.getenv("AIRTABLE_TABLE") or "视频分析"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 👉 生活 + 情绪 + 轻产品（混合）
KEYWORDS = [
    "dailyvlog",
    "dayinmylife",
    "cleangirl",
    "selfcare",
    "aesthetic",

    "生活日常",
    "我的一天",
    "治愈系",
    "压力释放",
    "女生生活",

    "perfumeroutine",
    "skincareroutine"
]

# ===== 搜索（用tag更稳定）=====
def search_videos(keyword):
    print(f"🔍 searching: {keyword}")

    tag = keyword.replace(" ", "")
    url = f"https://www.tiktok.com/tag/{tag}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()

        try:
            page.goto(url, timeout=60000)
            page.wait_for_timeout(6000)
        except:
            browser.close()
            return []

        links = page.eval_on_selector_all(
            "a[href*='/video/']",
            "els => els.map(e => e.href)"
        )

        browser.close()

    links = list(set(links))
    random.shuffle(links)

    print(f"🎥 found {len(links)} videos")
    return links[:5]


# ===== 抓视频 =====
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

        like = re.search(r'"diggcount":(\d+)', html)
        comment = re.search(r'"commentcount":(\d+)', html)
        title = re.search(r'<title>(.*?)</title>', html)

        browser.close()

        return {
            "url": url,
            "like": int(like.group(1)) if like else 0,
            "comment": int(comment.group(1)) if comment else 0,
            "title": title.group(1) if title else ""
        }


# ===== 判断是否值得分析 =====
def is_good(data):
    if data["like"] < 1000:
        return False
    if data["comment"] < 20:
        return False
    return True


# ===== 爆点分析（核心）=====
def analyze(data):
    text = data["title"]

    emotion = "普通"
    if any(x in text for x in ["stress", "压力", "tired", "累"]):
        emotion = "压力释放"
    elif any(x in text for x in ["happy", "love", "治愈"]):
        emotion = "治愈感"

    persona = "普通人"
    if any(x in text for x in ["that girl", "clean girl", "精致"]):
        persona = "精致人设"

    hook = "日常切入"
    if any(x in text for x in ["how", "tips", "方法"]):
        hook = "教学钩子"

    return {
        "emotion": emotion,
        "persona": persona,
        "hook": hook
    }


# ===== 自动生成内容方案 =====
def generate_idea(data, analysis):

    idea = f"{analysis['persona']}的一天 + {analysis['emotion']}"

    copy = f"我最近真的有点{analysis['emotion']}，所以开始这样生活…"

    shoot = "前3秒直接展示情绪 + 快节奏切换日常 + 结尾留空白引评论"

    return idea, copy, shoot


# ===== Telegram =====
def send_telegram(data, analysis, idea, copy, shoot):

    msg = f"""🔥 爆款参考

🎬 标题：
{data['title']}

🔗 {data['url']}

📊 数据：
👍 {data['like']}  💬 {data['comment']}

🧠 为什么会爆：
情绪：{analysis['emotion']}
人设：{analysis['persona']}
钩子：{analysis['hook']}

🎯 可复制选题：
{idea}

📝 文案开头：
{copy}

📹 拍法：
{shoot}
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
    print(f"🚀 total: {len(all_links)}")

    for link in all_links:

        data = scrape_video(link)

        if not data:
            continue

        if not is_good(data):
            continue

        analysis = analyze(data)
        idea, copy, shoot = generate_idea(data, analysis)

        send_telegram(data, analysis, idea, copy, shoot)

        time.sleep(random.randint(3,6))

    print("🔥 script finished")


if __name__ == "__main__":
    main()
