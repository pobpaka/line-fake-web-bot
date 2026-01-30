from flask import Flask, request, abort
import re

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

# ================== ใส่ค่าของคุณ ==================
LINE_CHANNEL_ACCESS_TOKEN = "l4IOYPa0HbfqOlwGVI0SZPchUyQ38RtBWiV+ahufQLVUC1R2NkJ1mGEyyo1cmEGKiMTTOlMWkc1WAYbuOcUkRVmkXA/ljBnOStgOGy/DOADUPSocUFWGE2rvQoFxOl16zYdGFrP7ZQ+A427B/7/eVQdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "97c6b5894f89ae844332d532ef07777d"
# ==================================================

app = Flask(__name__)

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ================== ฟังก์ชันเช็คเว็บปลอม ==================
def check_fake_url(url: str):
    score = 0
    reasons = []

    suspicious_domains = [
        "bit.ly", "tinyurl.com", "shorturl.at",
        ".xyz", ".top", ".click", ".online"
    ]

    phishing_words = [
        "login", "verify", "free", "bonus",
        "reward", "secure", "update", "bank"
    ]

    # ไม่ใช้ https
    if not url.startswith("https://"):
        score += 1
        reasons.append("❌ ไม่ใช้ https")

    # มี @ ใน URL
    if "@" in url:
        score += 2
        reasons.append("❌ มี @ ใน URL")

    # โดเมนต้องสงสัย
    for d in suspicious_domains:
        if d in url:
            score += 2
            reasons.append(f"❌ ใช้โดเมนต้องสงสัย ({d})")

    # คำล่อ
    for w in phishing_words:
        if w in url.lower():
            score += 1
            reasons.append(f"❌ พบคำล่อ '{w}'")

    return score, reasons

# ================== webhook ==================
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ================== รับข้อความจาก LINE ==================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text.strip()

    url_pattern = re.compile(r"https?://\S+")

    if url_pattern.search(user_text):
        score, reasons = check_fake_url(user_text)

        if score >= 4:
            status = "🔴 เสี่ยงสูงมาก (อาจเป็นเว็บปลอม)"
        elif score >= 2:
            status = "🟡 น่าสงสัย ควรระวัง"
        else:
            status = "🟢 ยังไม่พบความเสี่ยงชัดเจน"

        reply_text = (
            f"{status}\n\n"
            "🔍 ผลการตรวจสอบ:\n" +
            ("\n".join(reasons) if reasons else "ไม่พบสัญญาณอันตราย") +
            "\n\n⚠️ อย่ากรอกข้อมูลส่วนตัวหรือรหัสผ่าน"
        )
    else:
        reply_text = (
            "📌 ส่งลิงก์เว็บไซต์มาได้เลย\n"
            "ฉันจะช่วยตรวจว่าเสี่ยงเป็นเว็บปลอมหรือไม่"
        )

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

# ================== run ==================
if __name__ == "__main__":
    app.run(port=5000)
