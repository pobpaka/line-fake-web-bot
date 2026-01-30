from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from urllib.parse import urlparse
import os
import re

app = Flask(__name__)

# ================= ENV =================
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("Missing LINE environment variables")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ================= URL CHECK =================
URL_REGEX = re.compile(
    r'(https?://[^\s]+)',
    re.IGNORECASE
)

RISK_TLDS = ["xyz", "top", "click", "live", "loan", "vip"]
SCAM_WORDS = [
    "เครดิตฟรี", "free", "bonus", "slot", "casino",
    "login", "verify", "wallet", "update", "secure"
]

def extract_url(text):
    match = URL_REGEX.search(text)
    return match.group(1) if match else None

def analyze_url(url):
    score = 0
    reasons = []

    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()

    # root domain
    parts = domain.split(".")
    root_domain = ".".join(parts[-2:]) if len(parts) >= 2 else domain

    # 1. many dots
    if domain.count(".") >= 3:
        score += 1
        reasons.append("โดเมนมีหลายชั้นผิดปกติ")

    # 2. risky tld
    if root_domain.split(".")[-1] in RISK_TLDS:
        score += 2
        reasons.append("ใช้โดเมนระดับบนที่พบในเว็บหลอกลวงบ่อย")

    # 3. scam words in domain/path
    for w in SCAM_WORDS:
        if w in domain or w in path:
            score += 1
            reasons.append(f"พบคำชวนเชื่อ: {w}")
            break

    # 4. very long url
    if len(url) > 80:
        score += 1
        reasons.append("URL ยาวผิดปกติ")

    # 5. suspicious symbols
    if "-" in domain or "_" in domain:
        score += 1
        reasons.append("โดเมนมีสัญลักษณ์ที่ใช้ในเว็บปลอมบ่อย")

    # decision
    if score >= 4:
        level = "❌ เสี่ยงสูง (เข้าข่ายหลอกลวง)"
    elif score >= 2:
        level = "⚠️ น่าสงสัย (ควรระวัง)"
    else:
        level = "✅ ยังไม่พบความเสี่ยงชัดเจน"

    return level, reasons, root_domain

# ================= WEBHOOK =================
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ================= MESSAGE =================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    url = extract_url(text)

    if not url:
        reply = (
            "👋 ส่งลิงก์มาได้เลย\n"
            "ผมจะช่วยตรวจสอบความเสี่ยงให้ 🔍"
        )
    else:
        level, reasons, root = analyze_url(url)

        reply = f"🔍 ผลการตรวจสอบลิงก์\n\n"
        reply += f"🌐 โดเมนหลัก: {root}\n"
        reply += f"{level}\n\n"

        if reasons:
            reply += "📌 เหตุผลที่พบ:\n"
            for r in reasons:
                reply += f"• {r}\n"

        reply += "\n⚠️ คำแนะนำ:\n"
        reply += "อย่ากรอกข้อมูลส่วนตัว / รหัสผ่าน / OTP\n"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()
