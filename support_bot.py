# support_bot.py — VORN Support bot (python-telegram-bot v20+)

import os
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# === CONFIG ===
SUPPORT_BOT_TOKEN = os.getenv("SUPPORT_BOT_TOKEN", "").strip()
SUPPORT_ADMIN_ID = int(os.getenv("SUPPORT_ADMIN_ID", "0"))

if not SUPPORT_BOT_TOKEN:
    raise RuntimeError("SUPPORT_BOT_TOKEN env var is missing")
if not SUPPORT_ADMIN_ID:
    raise RuntimeError("SUPPORT_ADMIN_ID env var is missing or zero")

BOT_NAME = "VORN Support"

# === LOGGING ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# === HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = (
        f"👋 Hello {user.first_name or 'friend'}!\n\n"
        f"This is the {BOT_NAME} assistant.\n"
        f"Please describe your issue or question below, and our team will reply soon. 🕊"
    )
    await update.message.reply_text(msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or "(no text)"
    user_link = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

    admin_text = (
        f"📩 Message from user:\n"
        f"👤 <b>{user.full_name}</b>\n"
        f"🆔 <code>{user.id}</code>\n"
        f"🔗 {user_link}\n\n"
        f"💬 {text}"
    )

    try:
        # ուղարկում ենք ադմինին
        await context.bot.send_message(chat_id=SUPPORT_ADMIN_ID, text=admin_text, parse_mode="HTML")
        # փոքր դադար Telegram-ի սահմանափակումներից խուսափելու համար
        await asyncio.sleep(0.5)
        # պատասխանում ենք օգտվողին
        await update.message.reply_text("✅ Your message has been received.\nWe'll reply soon!")
    except Exception as e:
        logging.error(f"❌ Support send error: {e}")


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != SUPPORT_ADMIN_ID:
        await update.message.reply_text("⛔ You are not authorized to use this command.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage՝\n/reply <user_id> <message>")
        return

    try:
        uid = int(context.args[0])
        msg = " ".join(context.args[1:])
        await context.bot.send_message(chat_id=uid, text=msg, parse_mode="HTML")
        await asyncio.sleep(0.5)
        await update.message.reply_text("✅ Sent successfully.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send՝ {e}")


from telegram.request import HTTPXRequest

def build_support_app() -> Application:
    # ⚙️ կայուն կապերի համար ավելացնենք request configuration
    request = HTTPXRequest(
        connect_timeout=10.0,
        read_timeout=20.0,
        write_timeout=20.0,
        pool_timeout=15.0,
    )

    app = Application.builder().token(SUPPORT_BOT_TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", admin_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app


async def start_support_webhook():
    global support_app_global
    support_app_global = build_support_app()

    try:
        # Նախ webhook-ը ջնջենք ու նորից դնենք
        await support_app_global.bot.delete_webhook()
        await support_app_global.bot.set_webhook("https://vorn-bot-nggr.onrender.com/support")
        print("✅ Support bot webhook set successfully")
    except Exception as e:
        print(f"⚠️ Failed to set webhook: {e}")

    # --- Աշխատեցնենք բոտը նոր asyncio loop-ում (առանձին thread-ում)
    import threading, asyncio

    def run_asyncio_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(support_app_global.initialize())
        loop.create_task(support_app_global.start())
        print("🤖 Support bot started safely in background thread.")
        loop.run_forever()

    t = threading.Thread(target=run_asyncio_loop, name="support-bot-thread", daemon=True)
    t.start()


