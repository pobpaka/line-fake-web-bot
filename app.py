from flask import Flask, request, abort
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import hashlib
import requests
import re

# ===== ใส่ค่าจริงตรงนี้เลย =====
CHANNEL_ACCESS_TOKEN = "l4IOYPa0HbfqOlwGVI0SZPchUyQ38RtBWiV+ahufQLVUC1R2NkJ1mGEyyo1cmEGKiMTTOlMWkc1WAYbuOcUkRVmkXA/ljBnOStgOGy/DOADUPSocUFWGE2rvQoFxOl16zYdGFrP7ZQ+A427B/7/eVQdB04t89/1O/w1cDnyilFU="
CHANNEL_SECRET = "97c6b5894f89ae844332d532ef07777d"
# ==============================

app = Flask(__name__)

handler = WebhookHandler(CHANNEL_SECRET)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("ERROR:", e)
        abort(400)

    return "OK"

def is_suspicious_url(url: str) -> bool:
    suspicious_keywords = ["login", "verify", "secure", "update", "bank"]
    if any(k in url.lower() for k in suspicious_keywords):
        return True

    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return True
    except:
        return True

    return False

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    text = event.message.text.strip()

    urls = re.findall(r"https?://[^\s]+", text)

    if not urls:
        reply = "🔎 ส่งลิงก์มาได้เลย เดี๋ยวช่วยเช็กว่าเสี่ยงเว็บปลอมหรือไม่"
    else:
        results = []
        for url in urls:
            if is_suspicious_url(url):
                results.append(f"⚠️ {url}\nเสี่ยงเป็นเว็บปลอม")
            else:
                results.append(f"✅ {url}\nดูปกติ (เบื้องต้น)")

        reply = "\n\n".join(results)

    with ApiClient(configuration) as api_client:
        api = MessagingApi(api_client)
        api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )

if __name__ == "__main__":
    app.run(port=5000)
