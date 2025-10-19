# bot.py — VORN Coin (Mining + Referrals + Tasks)
# Python 3.10+, install: pip install python-telegram-bot==20.4

import os
import sqlite3
import time
from typing import Optional
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, jsonify, request
import threading
from flask_cors import CORS   # սա թույլ կտա խաղին հարցեր ուղարկել Flask-ին
app_web = Flask(__name__)
CORS(app_web)  # թույլ ենք տալիս խաղից գալու հարցումներ (Cross-Origin)


# --- Configuration ---
BOT_TOKEN  = "8419223502:AAF1Do1MjAA9R-A03Mbtamx49Nj19D6t76g"   # ← put your real BotFather token here
WEBAPP_URL = "https://68f527218aedde846923224c--roaring-longma-91e313.netlify.app/"
ADMIN_ID   =  5274439601   # you can later put your Telegram numeric ID for admin rights

COOLDOWN_SECONDS   = 60 * 60   # 1 hour mining cooldown
MINE_MIN, MINE_MAX = 1, 10
REF_BONUS_REFERRER = 10
REF_BONUS_NEWUSER  = 5
DB_PATH = "vorn.db"


# --- Database helpers ---
def db_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = db_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 0,
        referred_by INTEGER,
        joined_ts INTEGER,
        last_mine_ts INTEGER DEFAULT 0
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_id INTEGER,
        ts INTEGER
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        reward INTEGER NOT NULL,
        link TEXT,
        is_active INTEGER DEFAULT 1
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS task_completions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task_id INTEGER,
        ts INTEGER
    )""")
    conn.commit()
    conn.close()

def get_or_create_user(user_id: int, username: Optional[str] = None):
    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT user_id, username, balance, referred_by, joined_ts, last_mine_ts FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        now = int(time.time())
        c.execute("INSERT INTO users (user_id, username, balance, joined_ts) VALUES (?, ?, 0, ?)", (user_id, username, now))
        conn.commit()
        c.execute("SELECT user_id, username, balance, referred_by, joined_ts, last_mine_ts FROM users WHERE user_id=?", (user_id,))
        row = c.fetchone()
    conn.close()
    return row

def add_balance(user_id: int, amount: int):
    conn = db_conn(); c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit(); conn.close()

def set_last_mine(user_id: int, ts: int):
    conn = db_conn(); c = conn.cursor()
    c.execute("UPDATE users SET last_mine_ts=? WHERE user_id=?", (ts, user_id))
    conn.commit(); conn.close()

def set_referred_by(new_user_id: int, referrer_id: int):
    conn = db_conn(); c = conn.cursor()
    c.execute("UPDATE users SET referred_by=? WHERE user_id=? AND referred_by IS NULL", (referrer_id, new_user_id))
    conn.commit(); conn.close()

def save_referral(referrer_id: int, referred_id: int):
    conn = db_conn(); c = conn.cursor()
    c.execute("INSERT INTO referrals (referrer_id, referred_id, ts) VALUES (?, ?, ?)", (referrer_id, referred_id, int(time.time())))
    conn.commit(); conn.close()

def user_has_completed_task(user_id: int, task_id: int) -> bool:
    conn = db_conn(); c = conn.cursor()
    c.execute("SELECT 1 FROM task_completions WHERE user_id=? AND task_id=?", (user_id, task_id))
    ok = c.fetchone() is not None
    conn.close(); return ok

def complete_task(user_id: int, task_id: int, reward: int):
    conn = db_conn(); c = conn.cursor()
    c.execute("INSERT INTO task_completions (user_id, task_id, ts) VALUES (?, ?, ?)", (user_id, task_id, int(time.time())))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (reward, user_id))
    conn.commit(); conn.close()


# --- Bot logic ---
BOT_USERNAME = None

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Open Game", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton("🪙 Mine", callback_data="help_mine"),
         InlineKeyboardButton("💰 Balance", callback_data="help_balance")],
        [InlineKeyboardButton("👥 Referral", callback_data="help_ref"),
         InlineKeyboardButton("📋 Tasks", callback_data="help_tasks")],
    ])

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username)

    # այստեղ մենք ստեղծում ենք անհատական հղում՝ user_id-ով
    personal_url = f"{WEBAPP_URL}?user_id={user.id}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Open Game", web_app=WebAppInfo(url=personal_url))],
        [InlineKeyboardButton("💰 Balance", callback_data="help_balance"),
         InlineKeyboardButton("📋 Tasks", callback_data="help_tasks")],
    ])

    await update.message.reply_text(
        "🌕 Welcome to VORN Coin!\n\nClick below to open your mining app 👇",
        reply_markup=keyboard
    )


    # Referral check
    if args:
        payload = args[0]
        ref_id = None
        if payload.startswith("ref_"):
            try: ref_id = int(payload.split("ref_")[1])
            except: ref_id = None
        elif payload.isdigit():
            ref_id = int(payload)
        if ref_id and ref_id != user.id:
            row = get_or_create_user(user.id, user.username)
            if row[3] is None:
                set_referred_by(user.id, ref_id)
                save_referral(ref_id, user.id)
                add_balance(ref_id, REF_BONUS_REFERRER)
                add_balance(user.id, REF_BONUS_NEWUSER)

    await update.message.reply_text(
        "Welcome to VORN Coin 🌕\nTap below to open the WebApp or use commands below.",
        reply_markup=main_keyboard()
    )

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    await q.answer()
    messages = {
        "help_mine": f"Type /mine to collect coins every {COOLDOWN_SECONDS//60} minutes.",
        "help_balance": "Type /balance to see your current balance.",
        "help_ref": "Type /referral to get your invite link and stats.",
        "help_tasks": "Type /tasks to view active tasks and claim rewards."
    }
    if data in messages:
        await q.message.reply_text(messages[data])

async def mine_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import random
    user = update.effective_user
    row = get_or_create_user(user.id, user.username)
    last_ts = row[5] or 0
    now = int(time.time())
    if now - last_ts < COOLDOWN_SECONDS:
        rem = COOLDOWN_SECONDS - (now - last_ts)
        await update.message.reply_text(f"⏳ Wait {rem//60} more minutes before next mining.")
        return
    earned = random.randint(MINE_MIN, MINE_MAX)
    add_balance(user.id, earned)
    set_last_mine(user.id, now)
    await update.message.reply_text(f"🎉 You earned +{earned} points!")
    await balance_cmd(update, context)

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = get_or_create_user(user.id, user.username)
    await update.message.reply_text(f"💰 Your balance: {row[2]} points")

async def referral_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username)
    global BOT_USERNAME
    if BOT_USERNAME is None:
        me = await context.bot.get_me()
        BOT_USERNAME = me.username
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user.id}"
    conn = db_conn(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (user.id,))
    count = c.fetchone()[0]; conn.close()
    await update.message.reply_text(
        f"👥 Your invite link:\n{ref_link}\n\n"
        f"📈 People joined via you: {count}\n"
        f"🎁 Referral bonus — inviter: +{REF_BONUS_REFERRER}, new user: +{REF_BONUS_NEWUSER}"
    )

def list_active_tasks():
    conn = db_conn(); c = conn.cursor()
    c.execute("SELECT id, title, description, reward, link FROM tasks WHERE is_active=1 ORDER BY id ASC")
    rows = c.fetchall(); conn.close()
    return rows

async def tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_or_create_user(user.id, user.username)
    rows = list_active_tasks()
    if not rows:
        await update.message.reply_text("📋 No active tasks right now.")
        return
    await update.message.reply_text("📋 Active tasks (tap Claim after completing):")
    for task_id, title, desc, reward, link in rows:
        text = f"• {title} (+{reward})\n"
        if desc: text += f"{desc}\n"
        kb = InlineKeyboardMarkup([[
            *( [InlineKeyboardButton("🔗 Open", url=link)] if link else [] ),
            InlineKeyboardButton("✅ Claim", callback_data=f"claim:{task_id}")
        ]])
        await update.message.reply_text(text, reply_markup=kb)

async def claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    try:
        _, tid = q.data.split(":"); task_id = int(tid)
    except:
        await q.message.reply_text("❌ Invalid request."); return
    conn = db_conn(); c = conn.cursor()
    c.execute("SELECT reward FROM tasks WHERE id=? AND is_active=1", (task_id,))
    row = c.fetchone(); conn.close()
    if not row:
        await q.message.reply_text("❌ Task not found."); return
    reward = row[0]
    if user_has_completed_task(q.from_user.id, task_id):
        await q.message.reply_text("ℹ️ Already claimed.")
        return
    complete_task(q.from_user.id, task_id, reward)
    await q.message.reply_text(f"✅ Claimed! +{reward} points added.")
    fake = Update(update.update_id, message=q.message)
    await balance_cmd(fake, context)

async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db_conn(); c = conn.cursor()
    c.execute("SELECT username, balance FROM users ORDER BY balance DESC LIMIT 10")
    rows = c.fetchall(); conn.close()
    if not rows:
        await update.message.reply_text("No leaderboard yet."); return
    out = "🏆 Leaderboard\n\n"
    for i, (uname, bal) in enumerate(rows, start=1):
        out += f"{i}. {(uname or 'Anon')} — {bal}\n"
    await update.message.reply_text(out)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — open the WebApp\n"
        "/mine — mine coins\n"
        "/balance — check balance\n"
        "/referral — referral link\n"
        "/tasks — view tasks\n"
        "/leaderboard — top users\n"
        "/addtask — (admin) add task"
    )

async def addtask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_ID and update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only.")
        return
    raw = update.message.text[len("/addtask"):].strip()
    if not raw:
        await update.message.reply_text("Usage: /addtask Title | 20 | https://link | Description")
        return
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 2:
        await update.message.reply_text("Need at least: Title | Reward | [Link] | [Description]")
        return
    title = parts[0]
    try: reward = int(parts[1])
    except: await update.message.reply_text("Reward must be a number."); return
    link = parts[2] if len(parts) >= 3 and parts[2] else None
    desc = parts[3] if len(parts) >= 4 and parts[3] else None
    conn = db_conn(); c = conn.cursor()
    c.execute("INSERT INTO tasks (title, description, reward, link, is_active) VALUES (?, ?, ?, ?, 1)",
              (title, desc, reward, link))
    conn.commit(); conn.close()
    await update.message.reply_text(f"✅ Task added: “{title}” (+{reward})")

async def post_startup(app):
    global BOT_USERNAME
    me = await app.bot.get_me()
    BOT_USERNAME = me.username

# ----------------- Flask Web Server -----------------
app_web = Flask(__name__)

@app_web.route("/api/user/<int:user_id>")
def get_user_data(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, balance FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "User not found"}), 404

    username, balance = row
    return jsonify({
        "user_id": user_id,
        "username": username,
        "balance": balance
    })


@app_web.route("/api/mine", methods=["POST"])
def mine_api():
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id missing"}), 400
    ...

    # Բալանսի ավելացում
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "User not found"}), 404

    new_balance = row[0] + 1  # ամեն “Mine” սեղմումով 1 coin
    c.execute("UPDATE users SET balance=? WHERE user_id=?", (new_balance, user_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "balance": new_balance})

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, balance FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "User not found"}), 404
    username, balance = row
    return jsonify({"user_id": user_id, "username": username, "balance": balance})

def run_flask():
    app_web.run(host="0.0.0.0", port=8080)
# ----------------------------------------------------


def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_startup).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(help_callback, pattern="^help_"))
    app.add_handler(CommandHandler("mine", mine_cmd))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("referral", referral_cmd))
    app.add_handler(CommandHandler("tasks", tasks_cmd))
    app.add_handler(CallbackQueryHandler(claim_callback, pattern=r"^claim:\d+$"))
    app.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("addtask", addtask_cmd))
    print("✅ Bot is running (long polling)…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

def run_flask():
    app_web.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    main()


