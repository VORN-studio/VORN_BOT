# bot.py — VORN Bot (Render Webhook version)
import os, time, psycopg2
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =========================
# ENV + GLOBALS
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://vorn-bot-nggr.onrender.com").strip()
PORT = int(os.getenv("PORT", "10000"))

if not BOT_TOKEN or not DATABASE_URL:
    raise RuntimeError("❌ Missing BOT_TOKEN or DATABASE_URL")

ADMIN_IDS = {5274439601}
MINE_REWARD = 500
MINE_COOLDOWN = 6 * 60 * 60  # 6 hours

# =========================
# DB Helpers
# =========================
def db():
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    c = conn.cursor()
    c.execute("CREATE SCHEMA IF NOT EXISTS public; SET search_path TO public;")
    conn.commit()
    return conn

def init_db():
    conn = db(); c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            last_mine BIGINT DEFAULT 0,
            inviter_id BIGINT,
            vorn_balance REAL DEFAULT 0
        );
    """)
    conn.commit(); conn.close()
    print("✅ Database initialized successfully.")

def ensure_user(user_id, username):
    conn = db(); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id=%s", (user_id,))
    if not c.fetchone():
        c.execute("INSERT INTO users(user_id, username) VALUES(%s,%s)", (user_id, username))
    else:
        c.execute("UPDATE users SET username=%s WHERE user_id=%s", (username, user_id))
    conn.commit(); conn.close()

# =========================
# Telegram Handlers
# =========================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username)
    wa_url = f"{PUBLIC_BASE_URL}/app?uid={user.id}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌀 OPEN APP", web_app=WebAppInfo(url=wa_url))]
    ])
    await update.message.reply_text(
        "🌕 Welcome to the world of the future.\n\nPress the button below to enter the VORN App 👇",
        reply_markup=keyboard
    )
    await update.message.reply_text(f"✅ Connected successfully.\n🔗 {wa_url}")

async def btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("OK")

# =========================
# Flask Server + Webhook
# =========================
app = Flask(__name__, static_folder="webapp", static_url_path="")
CORS(app)

@app.route("/")
def home():
    return "✅ VORN Bot is alive via Render Webhook!", 200

@app.route("/webapp/<path:filename>")
def serve_static(filename):
    return send_from_directory("webapp", filename)

@app.route("/webhook", methods=["POST"])
def webhook():
    """Receive updates from Telegram and forward to bot"""
    try:
        update = Update.de_json(request.get_json(force=True), bot_instance)
        app_telegram.update_queue.put_nowait(update)
    except Exception as e:
        print("⚠️ Webhook error:", e)
    return "OK", 200

# =========================
# BOT SETUP (Webhook Mode)
# =========================
from telegram.ext import Application
import asyncio

async def setup_webhook():
    global bot_instance, app_telegram
    print("🤖 Initializing bot...")
    app_telegram = Application.builder().token(BOT_TOKEN).build()
    bot_instance = app_telegram.bot

    # Handlers
    app_telegram.add_handler(CommandHandler("start", start_cmd))
    app_telegram.add_handler(CallbackQueryHandler(btn_handler))

    # Set webhook URL
    wh_url = f"{PUBLIC_BASE_URL}/webhook"
    await bot_instance.delete_webhook(drop_pending_updates=True)
    await bot_instance.set_webhook(url=wh_url)
    print(f"✅ Webhook set successfully: {wh_url}")

    # Run the bot as background task
    asyncio.create_task(app_telegram.start())
    print("🟢 Bot background task started.")

# =========================
# MAIN ENTRY POINT
# =========================
if __name__ == "__main__":
    print("🛠️ Booting VORN Bot (Webhook Mode)...")
    init_db()

    # start async bot setup
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(setup_webhook())

    # run Flask server
    print(f"🚀 Flask server running on port {PORT}")
    app.run(host="0.0.0.0", port=PORT, threaded=True, use_reloader=False)
