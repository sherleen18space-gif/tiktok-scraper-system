import requests
import time
import urllib.parse

TELEGRAM_TOKEN = "你的token"
CHAT_ID = "你的chatid"

KEYWORDS = [
    "perfume girl",
    "smell good girl",
    "office girl routine",
    "that girl glow up",
    "self care girl",
    "tiktok made me buy it",
    "grwm",
    "kl girl style"
]


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })


def main():
    for kw in KEYWORDS:
        search_url = "https://www.tiktok.com/search?q=" + urllib.parse.quote(kw)

        msg = f"""🔥 今日选题方向

关键词: {kw}

👉 打开这个：
{search_url}

👉 看前5条视频

👉 判断：
1. 有没有女生情绪（累 / 想变好）
2. 有没有“被注意 / 被记住”
3. 能不能改成：
   KL女生 + 香味吸引

👉 拍的时候：
- 用男生视角（你优势🔥）
- 不讲产品，只讲感觉

"""
        send_telegram(msg)
        time.sleep(1)


if __name__ == "__main__":
    main()
