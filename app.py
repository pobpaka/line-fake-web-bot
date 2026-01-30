from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage
)
import os
import re
import requests

app = Flask(__name__)

# ====== LINE ENV ======
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("l4IOYPa0HbfqOlwGVI0SZPchUyQ38RtBWiV+ahufQLVUC1R2NkJ1mGEyyo1cmEGKiMTTOlMWkc1WAYbuOcUkRVmkXA/ljBnOStgOGy/DOADUPSocUFWGE2rvQoFxOl16zYdGFrP7ZQ+A427B/7/eVQdB04t89/1O/w1cDnyilFU=")
LINE_CHANNEL_SECRET = os.getenv("97c6b5894f89ae844332d532ef07777d")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ====== ฟังก์ชันเช็กว่าเป็น URL ไหม ======
def is_url(text):
    url_pattern = re.compile(
        r'^(https?:\/\/)?([\w\-]+\.)+[\w\-]+(\/[\w\-._~:/?#[\]@!$&\'()*+,;=]*)?$'
    )
    return re.match(url_pattern, text)

# ====== ฟังก์ชันตรวจเว็บปลอม (ตัวอย่างง่าย) ======
def check_website(url):
    # blacklist ตัวอย่าง (คุณเพิ่มเองได้)
    blacklist = [
        "free-money",
        "login-facebook",
        "secure-update",
        "bit.ly",
        "tinyurl"
    ]

    for bad in blacklist:
        if bad in url.lower():
            return "danger"

    return "safe"


# ====== webhook ======
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# ====== รับข้อความจากผู้ใช้ ======
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    # ถ้าไม่ใช่ลิงก์
    if not is_url(user_text):
        reply_text = (
            "👋 สวัสดีครับ\n\n"
            "🔎 ผมคือบอทตรวจสอบเว็บปลอม\n"
            "กรุณาส่ง *ลิงก์เว็บไซต์* มาเพื่อตรวจสอบ\n\n"
            "⚠️ ระวังเว็บหลอกลวง"
        )
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        return

    # ถ้าเป็นลิงก์ → ตรวจสอบ
    status = check_website(user_text)

    if status == "safe":
        reply_text = (
            "✅ ผลการตรวจสอบ\n\n"
            "เว็บไซต์นี้ *ยังไม่พบรายงานว่าเป็นเว็บปลอม*\n\n"
            "ℹ️ แนะนำ: ตรวจสอบ URL และชื่อโดเมนทุกครั้ง"
        )
    else:
        reply_text = (
            "❌ คำเตือน!\n\n"
            "เว็บไซต์นี้ *มีความเสี่ยงสูง*\n"
            "อาจเป็นเว็บปลอมหรือเว็บหลอกลวง\n\n"
            "🚫 ห้ามกรอกข้อมูลส่วนตัวเด็ดขาด"
        )

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )


# ====== RUN ======
if __name__ == "__main__":
    app.run()
