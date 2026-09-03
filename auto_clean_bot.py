"""
Telegram guruhidagi keraksiz TIZIM xabarlarini avtomatik o'chiruvchi bot.
Oddiy foydalanuvchi yozgan xabarlarga umuman tegmaydi.

O'CHIRILADIGAN XABARLAR TURI:
    1) Telegramning o'zi yaratadigan haqiqiy tizim xabarlari:
       - "X guruhga qo'shildi" / "X guruhni tark etdi"
       - "X xabarni qadadi" (pin)
       - Guruh nomi/rasmi o'zgargani haqidagi xabarlar
       - Video chat boshlandi/tugadi haqidagi xabarlar

    2) Boshqa BOTLAR (masalan ANI_HEN kabi) yuboradigan, tizim xabariga
       o'xshatib yozilgan lekin aslida ODDIY MATN bo'lgan xabarlar
       (BOT_NOTICE_PHRASES ro'yxati orqali). Bu tekshiruv FAQAT bot
       yuborgan xabarlarda ishlaydi - oddiy odam yozgan xabarga hech
       qachon tegmaydi.

RENDER'GA JOYLASHTIRISH:
    1. Ushbu fayl + requirements.txt + runtime.txt ni GitHub repo'ga joylang.
    2. Render.com > New > Web Service > repo'ni tanlang.
    3. Environment Variables bo'limiga qo'shing:
         BOT_TOKEN = <sizning bot tokeningiz>
         PYTHON_VERSION = 3.11.9
    4. Start Command: python auto_clean_bot.py
    5. Deploy qiling.
"""

import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tokenni environment variable'dan oladi (Render'da shunday sozlanadi)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "SIZNING_BOT_TOKENINGIZ")

# Boshqa botlar yuboradigan, tizim xabariga o'xshatilgan matnli
# bildirishnomalar shu yerda ro'yxatga olinadi (kichik harflarda).
BOT_NOTICE_PHRASES = [
    "xabarni qadadi",
    "guruhni tark etdi",
    "guruhga qo'shildi",
    "guruhga qoshildi",
]


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start bosilganda foydalanuvchiga botdan qanday foydalanish haqida ma'lumot beradi."""
    text = (
        "\U0001F44B Salom!\n\n"
        "Men guruhlardagi keraksiz *tizim xabarlarini* avtomatik o'chiruvchi botman.\n\n"
        "\U0001F9F9 Nimalarni o'chiraman:\n"
        "- \"guruhga qo'shildi\" / \"guruhni tark etdi\" xabarlari\n"
        "- \"xabarni qadadi\" (pin) xabarlari\n"
        "- guruh nomi/rasmi o'zgargani haqidagi xabarlar\n"
        "- boshqa botlar yuboradigan shunga o'xshash bildirishnomalar\n\n"
        "\u2699\uFE0F Sozlash uchun:\n"
        "1. Meni guruhingizga qo'shing\n"
        "2. Meni *admin* qiling\n"
        "3. Admin huquqlarida albatta \"Xabarlarni o'chirish\" yoqilgan bo'lsin\n\n"
        "Shundan so'ng men guruhni avtomatik tozalab boraman \u2705"
    )
    await update.effective_message.reply_text(text, parse_mode="Markdown")


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


async def delete_bot_notice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Boshqa BOTLAR yuborgan, tizim xabariga o'xshatilgan matnli xabarlarni o'chiradi.
    Faqat message.from_user.is_bot=True bo'lganda ishlaydi - oddiy odam yozgan
    xabarga hech qachon tegmaydi."""
    msg = update.effective_message
    if not msg or not msg.text:
        return
    sender = msg.from_user
    if not sender or not sender.is_bot:
        return

    text_lower = msg.text.lower()
    for phrase in BOT_NOTICE_PHRASES:
        if phrase in text_lower:
            try:
                await msg.delete()
                logger.info("Bot bildirishnomasi o'chirildi: %s", msg.text[:50])
            except Exception as e:
                logger.warning("O'chirib bo'lmadi: %s", e)
            return


# ---- Render uchun oddiy health-check server (PORT ochiq turishi kerak) ----
def run_health_server():
    port = int(os.environ.get("PORT", 10000))

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot ishlayapti")

        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()

        def log_message(self, format, *args):
            pass  # konsolni tozalab turish uchun

    HTTPServer(("0.0.0.0", port), Handler).serve_forever()


def main():
    threading.Thread(target=run_health_server, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))

    # 1) Telegramning haqiqiy tizim xabarlari
    app.add_handler(MessageHandler(filters.StatusUpdate.ALL, delete_service_message))

    # 2) Boshqa botlar yuborgan, tizim xabariga o'xshatilgan matnli xabarlar
    app.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS, delete_bot_notice)
    )

    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
