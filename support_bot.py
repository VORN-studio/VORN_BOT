# support_bot.py — VORN Support bot (python-telegram-bot v20+)

import os
import logging
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
    # Ուղարկում ենք ադմինին
    await context.bot.send_message(chat_id=SUPPORT_ADMIN_ID, text=admin_text, parse_mode="HTML")
    # Պատասխանում ենք օգտվողին
    await update.message.reply_text("✅ Your message has been received.\nWe'll reply soon!")

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != SUPPORT_ADMIN_ID:
        return await update.message.reply_text("⛔ You are not authorized to use this command.")
    if len(context.args) < 2:
        return await update.message.reply_text("Usage՝\n/reply <user_id> <message>")
    try:
        uid = int(context.args[0])
        msg = " ".join(context.args[1:])
        await context.bot.send_message(chat_id=uid, text=msg, parse_mode="HTML")
        await update.message.reply_text("✅ Sent successfully.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send՝ {e}")

def build_support_app() -> Application:
    app = Application.builder().token(SUPPORT_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", admin_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app

async def start_support_webhook():
    app = build_support_app()
    await app.bot.delete_webhook()
    await app.bot.set_webhook("https://vorn-bot-nggr.onrender.com/support")
    print("✅ Support bot webhook set successfully")
