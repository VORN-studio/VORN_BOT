# support_bot.py — VORN Support bot (python-telegram-bot v20+)

import os
import logging
import asyncio
import threading
from typing import Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.request import HTTPXRequest

# === CONFIG ===
SUPPORT_BOT_TOKEN = os.getenv("SUPPORT_BOT_TOKEN", "").strip()
SUPPORT_ADMIN_ID = int(os.getenv("SUPPORT_ADMIN_ID", "0"))
SUPPORT_WEBHOOK_URL = "https://vorn-bot-nggr.onrender.com/support"

if not SUPPORT_BOT_TOKEN:
    raise RuntimeError("SUPPORT_BOT_TOKEN env var is missing")
if not SUPPORT_ADMIN_ID:
    raise RuntimeError("SUPPORT_ADMIN_ID env var is missing or zero")

BOT_NAME = "DOMINO Support"

# === LOGGING ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# === HANDLԵRS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = (
        f"👋 Привет, {user.first_name or 'друг'}!\n\n"
        f"Это ассистент {BOT_NAME} .\n"
        f"Пожалуйста, опишите вашу проблему или вопрос ниже, и наша команда скоро ответит. 🕊"
    )
    await update.message.reply_text(msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or "(no text)"
    user_link = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

    admin_text = (
        f"📩 Сообщение от пользователя:\n"
        f"👤 <b>{user.full_name}</b>\n"
        f"🆔 <code>{user.id}</code>\n"
        f"🔗 {user_link}\n\n"
        f"💬 {text}"
    )
    try:
        await context.bot.send_message(chat_id=SUPPORT_ADMIN_ID, text=admin_text, parse_mode="HTML")
        await asyncio.sleep(0.2)
        await update.message.reply_text("✅ Ваше обращение принято.\nМы ответим вам в ближайшее время!")
    except Exception as e:
        logging.error(f"❌ Ошибка при отправке в поддержку: {e}")

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != SUPPORT_ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет прав для использования этой команды.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Использование՝\n/reply <user_id> <message>")
        return
    try:
        uid = int(context.args[0])
        msg = " ".join(context.args[1:])
        await context.bot.send_message(chat_id=uid, text=msg, parse_mode="HTML")
        await asyncio.sleep(0.1)
        await update.message.reply_text("✅ Сообщение успешно отправлено.")
    except Exception as e:
        await update.message.reply_text(f"❌ Не удалось отправить сообщение՝ {e}")

# === Runtime (թել + իր loop) ===

_support_loop: Optional[asyncio.AbstractEventLoop] = None
_support_app: Optional[Application] = None

def _build_app() -> Application:
    # httpx v0.24.1 համար ճիշտ պարամետրերը — pool_limits չկա
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

def start_support_runtime():
    """
    Սկսում է support բոտը առանձին թելով և իր event loop-ով:
    Flask-ից update-ը հետո կտանք այս loop-ին (cross-thread safe):
    """
    global _support_loop, _support_app

    def runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        app = _build_app()
        async def init():
            await app.initialize()
            # Webhook configure այստեղ, նույն loop-ում
            try:
                await app.bot.delete_webhook()
                await app.bot.set_webhook(SUPPORT_WEBHOOK_URL)
                print("✅ Support bot webhook set successfully")
            except Exception as e:
                print(f"⚠️ Failed to set support webhook: {e}")
            await app.start()
            print("🤖 Support bot is running")

        loop.run_until_complete(init())

        # պահում ենք գլոբալ հղումները հենց այս թելում ստեղծված օբյեկտներով
        globals()['_support_loop'] = loop
        globals()['_support_app'] = app

        # run forever
        loop.run_forever()

    t = threading.Thread(target=runner, name="support-bot-thread", daemon=True)
    t.start()

def enqueue_support_update(update_json: dict):
    """
    Կոչ է արվում Flask route-ից.
    Update-ը serialize/dejson ենք անում support բոտի bot-ով
    և process_update-ը տրվում է support loop-ին անվտանգ ձևով:
    """
    if _support_app is None or _support_loop is None:
        raise RuntimeError("Support bot is not started yet")

    upd = Update.de_json(update_json, _support_app.bot)
    # Չենք սպասում, queuing-only (արագ 200 վերադարձնելու համար)
    asyncio.run_coroutine_threadsafe(_support_app.process_update(upd), _support_loop)
