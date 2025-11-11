# support_bot.py — minimal Telegram support bot
# pip install python-telegram-bot==20.3

import logging
from telegram import Update, ForceReply
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# === CONFIG ===
import os

SUPPORT_BOT_TOKEN = os.getenv("SUPPORT_BOT_TOKEN", "").strip()
SUPPORT_ADMIN_ID = int(os.getenv("SUPPORT_ADMIN_ID", "0"))
if not SUPPORT_BOT_TOKEN:
    raise RuntimeError("SUPPORT_BOT_TOKEN env var is missing")

BOT_NAME = "VORN Support"

# === LOGGING ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# === START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = (
        f"👋 Hello {user.first_name or 'there'}!\n\n"
        f"This is the official {BOT_NAME} assistant.\n"
        f"Please describe your issue or question below.\n"
        f"Our team will get back to you soon. 🕊"
    )
    await update.message.reply_text(msg)

# === FORWARD USER MESSAGES TO ADMIN ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or "(no text)"
    print(f"📨 Message received from {user.id}: {text}")

    user_link = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

    # Send user message to admin
    admin_text = (
        f"📩 Message from user:\n"
        f"👤 <b>{user.full_name}</b>\n"
        f"🆔 <code>{user.id}</code>\n"
        f"🔗 {user_link}\n\n"
        f"💬 {text}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")

    # Auto reply to user
    await update.message.reply_text("✅ Your message has been received.\nWe'll reply soon!")

# === ADMIN CAN REPLY ===
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ You are not authorized.")
    if len(context.args) < 2:
        return await update.message.reply_text("Usage:\n/reply <user_id> <message>")
    try:
        uid = int(context.args[0])
        msg = " ".join(context.args[1:])
        await context.bot.send_message(
    chat_id=uid,
    text=msg,
    parse_mode="HTML"
)

        await update.message.reply_text("✅ Sent.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")

# === MAIN ===
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", admin_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ {BOT_NAME} is running...")
    app.run_polling()

# if __name__ == "__main__":
 #   main()
