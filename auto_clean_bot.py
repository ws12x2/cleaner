"""
Telegram guruhidagi TIZIM (service) xabarlarini avtomatik o'chiruvchi bot.
Oddiy foydalanuvchi yozgan xabarlarga umuman tegmaydi.

O'CHIRILADIGAN XABARLAR TURI (Telegramning o'zi yaratadigan):
    - "X guruhga qo'shildi"
    - "X guruhni tark etdi"
    - "X xabarni qadadi" (pinned message)
    - "Guruh nomi o'zgartirildi"
    - "Guruh rasmi o'zgartirildi / o'chirildi"
    - Video chat boshlandi/tugadi haqidagi xabarlar
    - va boshqa shunga o'xshash avtomatik xabarlar

RENDER'GA JOYLASHTIRISH:
    1. Ushbu fayl + requirements.txt ni GitHub repo'ga joylang.
    2. Render.com > New > Web Service > repo'ni tanlang.
    3. Environment Variables bo'limiga qo'shing:
         BOT_TOKEN = <sizning bot tokeningiz>
    4. Start Command: python auto_clean_bot.py
    5. Deploy qiling.

    Eslatma: Render "Web Service" doim ochiq PORT talab qiladi, shuning
    uchun quyida oddiy health-check server ham ishga tushiriladi (bot
    ishlab turganini ko'rsatish uchun). Buni o'zgartirish shart emas.
"""

import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tokenni environment variable'dan oladi (Render'da shunday sozlanadi)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")


async def delete_service_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Har qanday Telegram tizim xabarini (pin, join, leave, va h.k.) o'chiradi."""
    msg = update.effective_message
    if not msg:
        return
    try:
        await msg.delete()
        logger.info("Tizim xabari o'chirildi (chat_id=%s)", msg.chat_id)
    except Exception as e:
        logger.warning("O'chirib bo'lmadi: %s", e)


# ---- Render uchun oddiy health-check server (PORT ochiq turishi kerak) ----
def run_health_server():
    port = int(os.environ.get("PORT", 10000))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot ishlayapti")

        def log_message(self, format, *args):
            pass  # konsolni tozalab turish uchun

    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


def main():
    threading.Thread(target=run_health_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # filters.StatusUpdate.ALL - Telegramning barcha tizim xabarlarini qamrab oladi:
    # new_chat_members, left_chat_member, pinned_message, new_chat_title,
    # new_chat_photo, delete_chat_photo, video_chat_started/ended va h.k.
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, delete_service_message))

    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
