# bot.py — VORN Coin (Telegram Bot + Flask WebApp)
# Python 3.10+  |  pip install flask flask-cors python-telegram-bot==20.3

import os
import psycopg2
import time
import threading
from typing import Optional

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS




# =========================
# Flask Web Server
# =========================
app_web = Flask(__name__, static_folder=None)
CORS(app_web)

# --- FIX: Add universal home and catch-all routes ---
@app_web.route("/")
def index():
    return "✅ VORN Bot is online (Render active). Go to /app for interface.", 200

@app_web.route("/<path:anypath>")
def catch_all(anypath):
    # Redirect all unknown routes (like /privacy or /tasks) to home
    return "✅ VORN Bot is running. Unknown path: /" + anypath, 200
# ----------------------------------------------------


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEBAPP_DIR = os.path.join(BASE_DIR, "webapp")  # contains index.html, app.js, style.css, assets/


@app_web.route("/app")
def app_page():
    # serve the SPA entry
    return send_from_directory(WEBAPP_DIR, "index.html")

# Serve static files under /webapp/*
@app_web.route("/webapp/<path:filename>")
def serve_webapp(filename):
    # canonical single route for all webapp files
    resp = send_from_directory(WEBAPP_DIR, filename)
    # perf/caching hints
    if filename.endswith(".mp4"):
        resp.headers["Cache-Control"] = "public, max-age=86400"
        resp.headers["Accept-Ranges"] = "bytes"
        resp.headers["Content-Type"] = "video/mp4"
    elif filename.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        resp.headers["Cache-Control"] = "public, max-age=86400"
    elif filename.endswith((".css", ".js")):
        resp.headers["Cache-Control"] = "no-cache"
    return resp

# favicon (optional)
@app_web.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(WEBAPP_DIR, "assets"), "favicon.ico")

# =========================
# Telegram Bot
# =========================
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram import Bot

print("✅ Bot script loaded successfully.")

# ---- Config / ENV ----
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var is missing. Set it before running the bot.")

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip()
if not PUBLIC_BASE_URL:
    PUBLIC_BASE_URL = "https://vorn-bot-nggr.onrender.com"

ADMIN_IDS = {5274439601}
DB_PATH = os.path.join(BASE_DIR, "vorn.db")

# Mining
MINE_COOLDOWN = 6 * 60 * 60  # 6 hours
MINE_REWARD = 500

# =========================
# Database
# =========================
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing!")

def db():
    conn = psycopg2.connect(DATABASE_URL, sslmode="require")
    conn.autocommit = True  # ✅ prevents "InFailedSqlTransaction"
    c = conn.cursor()
    try:
        c.execute("CREATE SCHEMA IF NOT EXISTS public;")
        c.execute("SET search_path TO public;")
    except Exception as e:
        print("⚠️ DB schema check error:", e)
    return conn



def init_db():
    print("🛠️ Running init_db() ...")
    conn = db()
    c = conn.cursor()


    c.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0,
    last_mine BIGINT DEFAULT 0,
    language TEXT DEFAULT 'en',
    intro_seen BOOLEAN DEFAULT FALSE,
    last_reminder_sent BIGINT DEFAULT 0,
    inviter_id BIGINT,
    vorn_balance REAL DEFAULT 0
)
""")


    c.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    type TEXT,
    title TEXT,
    reward INTEGER,
    link TEXT,
    description TEXT,
    verifier TEXT,
    required BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    created_at BIGINT
)
""")


    c.execute("""
CREATE TABLE IF NOT EXISTS user_tasks (
    user_id BIGINT,
    task_id BIGINT,
    date_key TEXT,
    completed_at BIGINT,
    PRIMARY KEY (user_id, task_id, date_key)
)
""")


    # safe alters (ignore if exist)
    alters = [
        "ALTER TABLE users ADD COLUMN inviter_id INTEGER DEFAULT NULL",
        "CREATE INDEX IF NOT EXISTS idx_users_inviter ON users(inviter_id)",
        "ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'en'",
        "ALTER TABLE users ADD COLUMN intro_seen INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN last_reminder_sent INTEGER DEFAULT 0",
        "ALTER TABLE tasks ADD COLUMN verifier TEXT",
        "ALTER TABLE tasks ADD COLUMN required INTEGER DEFAULT 0",
        "ALTER TABLE tasks ADD COLUMN created_at INTEGER",
        "ALTER TABLE tasks ADD COLUMN active INTEGER DEFAULT 1",
    ]
    for sql in alters:
        try: c.execute(sql)
        except Exception: pass

        conn.commit()
    conn.close()
    print("✅ Tables created successfully in PostgreSQL.")


def acquire_bot_lock() -> bool:
    """
    Ensures only ONE poller runs worldwide.
    Returns True if we got the lock (safe to start polling),
    False if another instance is already polling.
    """
    try:
        conn = db(); c = conn.cursor()
        # Use a constant app-wide key. Any BIGINT OK; choose a stable “random” number.
        c.execute("SELECT pg_try_advisory_lock(905905905905)")
        got = c.fetchone()[0]
        conn.commit(); conn.close()
        return bool(got)
    except Exception as e:
        print(f"⚠️ advisory_lock error: {e}")
        # If DB is unreachable, better avoid starting multiple pollers
        return False

def release_bot_lock():
    """Optional: release on clean exit (not strictly needed on Render restarts)."""
    try:
        conn = db(); c = conn.cursor()
        c.execute("SELECT pg_advisory_unlock(905905905905)")
        conn.commit(); conn.close()
    except Exception:
        pass

    

def ensure_user(user_id: int, username: Optional[str], inviter_id: Optional[int] = None):
    conn = db(); c = conn.cursor()
    c.execute("SELECT user_id, inviter_id FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone()
    if row is None:
        c.execute("""
            INSERT INTO users (user_id, username, balance, last_mine, language, intro_seen, last_reminder_sent, inviter_id)
            VALUES (%s, %s, 0, 0, 'en', 0, 0, %s)
        """, (user_id, username, inviter_id))
    else:
        old_inviter = row[1]
        if old_inviter is None and inviter_id:
            c.execute("UPDATE users SET inviter_id=%s WHERE user_id=%s", (inviter_id, user_id))
        c.execute("UPDATE users SET username=%s WHERE user_id=%s", (username, user_id))
    conn.commit()
    conn.close()


def get_balance(user_id: int) -> int:
    conn = db(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def update_balance(user_id: int, delta: int) -> int:
    conn = db(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone()
    if not row:
        new_balance = int(delta)
        c.execute("INSERT INTO users (user_id, balance) VALUES (%s, %s)", (user_id, new_balance))
    else:
        new_balance = int(row[0]) + int(delta)
        c.execute("UPDATE users SET balance=%s WHERE user_id=%s", (new_balance, user_id))
    conn.commit()
    conn.close()
    return new_balance



def can_mine(user_id: int):
    """
    Returns (True, 0) if user can mine now,
    else (False, remaining_seconds)
    """
    now = int(time.time())
    conn = db(); c = conn.cursor()
    c.execute("SELECT last_mine FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone()
    last_mine = row[0] if row and row[0] else 0
    conn.close()

    # 6 ժամ = 21600 վայրկյան
    diff = now - last_mine
    if diff >= MINE_COOLDOWN:
        return True, 0
    else:
        return False, MINE_COOLDOWN - diff


def set_last_mine(user_id: int):
    now = int(time.time())
    conn = db(); c = conn.cursor()
    c.execute("UPDATE users SET last_mine=%s, last_reminder_sent=0 WHERE user_id=%s", (now, user_id))
    conn.commit()
    conn.close()


# =========================
# Minimal JSON API (webapp uses it)
# =========================
@app_web.route("/api/user/<int:user_id>")
def api_get_user(user_id):
    conn = db(); c = conn.cursor()
    c.execute("SELECT username, balance, last_mine, language, vorn_balance FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone(); conn.close()

    if not row:
        return jsonify({"error": "User not found"}), 404

    username, balance, last_mine, language, vorn_balance = row
    return jsonify({
        "user_id": user_id,
        "username": username,
        "balance": balance,
        "last_mine": last_mine,
        "language": language or "en",
        "vorn_balance": vorn_balance or 0
    })



@app_web.route("/api/set_language", methods=["POST"])
def api_set_language():
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    lang = (data.get("language") or "en")[:8]
    if not user_id:
        return jsonify({"ok": False, "error": "missing user_id"}), 400
    conn = db(); c = conn.cursor()
    c.execute("UPDATE users SET language=%s WHERE user_id=%s", (lang, user_id))
    conn.commit(); conn.close()
    return jsonify({"ok": True})

@app_web.route("/api/mine", methods=["POST"])
def api_mine():
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    if not user_id:
        return jsonify({"ok": False, "error": "missing user_id"}), 400

    ok, remaining = can_mine(user_id)
    if not ok:
        return jsonify({"ok": False, "cooldown": remaining}), 200

    new_bal = update_balance(user_id, MINE_REWARD)
    set_last_mine(user_id)
    now_ts = int(time.time())

    return jsonify({
        "ok": True,
        "reward": MINE_REWARD,
        "balance": new_bal,
        "last_mine": now_ts
    }), 200



@app_web.route("/api/mine_click", methods=["POST"])
def api_mine_click():
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    if not user_id:
        return jsonify({"ok": False, "error": "missing user_id"}), 400

    new_bal = update_balance(user_id, 1)
    return jsonify({"ok": True, "reward": 1, "balance": new_bal}), 200

@app_web.route("/api/vorn_reward", methods=["POST"])
def api_vorn_reward():
    """
    Called when progress bar reaches 100%.
    Adds +0.02 VORN (🜂) to user and saves it in DB.
    """
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    amount = float(data.get("amount", 0.02))

    if not user_id:
        return jsonify({"ok": False, "error": "missing user_id"}), 400

    try:
        conn = db()
        c = conn.cursor()

        # ensure user row exists
        c.execute("SELECT vorn_balance FROM users WHERE user_id=%s", (user_id,))
        row = c.fetchone()
        if not row:
            c.execute("INSERT INTO users (user_id, vorn_balance) VALUES (%s, %s)", (user_id, amount))
            vbal = amount
        else:
            vbal = (row[0] if row[0] else 0.0) + amount
            c.execute("UPDATE users SET vorn_balance=%s WHERE user_id=%s", (vbal, user_id))

        conn.commit()
        conn.close()
        print(f"🜂 Added {amount} VORN to {user_id}, new total = {vbal}")
        return jsonify({"ok": True, "vorn_added": amount, "vorn_balance": vbal})

    except Exception as e:
        print("🔥 /api/vorn_reward failed:", e)
        return jsonify({"ok": False, "error": str(e)}), 500



@app_web.route("/api/vorn_exchange", methods=["POST"])
def api_vorn_exchange():
    """
    Converts Feathers (🪶) into VORN (🜂)
    50_000 Feathers = 1 🜂
    """
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    if not user_id:
        return jsonify({"ok": False, "error": "missing user_id"}), 400

    COST = 50000      # 🪶 required per conversion
    REWARD = 1.0      # 🜂 gained

    conn = db()
    c = conn.cursor()

    # ensure vorn_balance column exists
    try:
        c.execute("ALTER TABLE users ADD COLUMN vorn_balance REAL DEFAULT 0")
    except Exception:
        pass

    # read current balances
    c.execute("SELECT balance, vorn_balance FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"ok": False, "error": "user not found"}), 404

    feathers, vorn = row
    if feathers < COST:
        conn.close()
        return jsonify({"ok": False, "error": f"not enough feathers (need {COST})"}), 400

    # do exchange
    new_feathers = feathers - COST
    new_vorn = vorn + REWARD

    c.execute(
        "UPDATE users SET balance=%s, vorn_balance=%s WHERE user_id=%s",
        (new_feathers, new_vorn, user_id)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "spent_feathers": COST,
        "new_balance": new_feathers,
        "new_vorn": new_vorn
    })

@app_web.route("/api/tasks")
def api_tasks():
    """Return all active tasks grouped by type + user's completion state."""
    uid = int(request.args.get("uid", 0))

    conn = db(); c = conn.cursor()

    # ensure columns exist
    for sql in [
        "ALTER TABLE tasks ADD COLUMN reward_feather INTEGER DEFAULT 0",
        "ALTER TABLE tasks ADD COLUMN reward_vorn REAL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN vorn_balance REAL DEFAULT 0"
    ]:
        try: c.execute(sql)
        except Exception: pass

    # get all tasks
    c.execute("""
        SELECT id, type, title, reward_feather, reward_vorn, link
        FROM tasks
        WHERE active = TRUE
        ORDER BY id DESC
    """)

    rows = c.fetchall()

    # user's completed tasks
    user_done = set()
    if uid:
        date_key = time.strftime("%Y-%m-%d")
        c.execute("SELECT task_id FROM user_tasks WHERE user_id=%s AND date_key=%s", (uid, date_key))
        for r in c.fetchall():
            user_done.add(r[0])

    data = {"main": [], "daily": []}
    for row in rows:
        tid, ttype, title, rf, rv, link = row
        entry = {
            "id": tid,
            "title": title,
            "reward_feather": rf,
            "reward_vorn": rv,
            "link": link or "",
            "completed": tid in user_done
        }
        if ttype not in data:
            data[ttype] = []
        data[ttype].append(entry)

    conn.close()
    return jsonify(data)


@app_web.route("/api/ref_link/<int:user_id>")
def api_ref_link(user_id: int):
    bot_username = os.getenv("BOT_USERNAME", "VORNCoinbot").lstrip("@")
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    return jsonify({"ok": True, "link": ref_link})

# =========================
# Admin Task helpers (placeholders)
# =========================
def add_task_db(task_type, title, reward, link=None, description=None, verifier="tg_join", required=0):
    conn = db(); c = conn.cursor()
    c.execute("""
        INSERT INTO tasks (type, title, reward, link, description, verifier, required, created_at, active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
    """, (task_type, title, int(reward), link, description, verifier, int(required), int(time.time())))
    conn.commit(); conn.close()

def list_tasks(task_type: str):
    conn = db(); c = conn.cursor()
    c.execute("""
        SELECT id, title, reward, link, description
        FROM tasks
        WHERE type=%s AND active=1
        ORDER BY id DESC
    """, (task_type,))
    rows = c.fetchall(); conn.close()
    return rows


# =========================
# Telegram Handlers
# =========================
def parse_start_payload(text: Optional[str]) -> Optional[int]:
    if not text: return None
    parts = text.strip().split(maxsplit=1)
    if len(parts) < 2: return None
    payload = parts[1]
    if payload.startswith("ref_"):
        try: return int(payload.replace("ref_", "", 1))
        except Exception: return None
    return None

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user or (update.message.from_user if update.message else None)
    if not user: return
    ensure_user(user.id, user.username)

    base = (PUBLIC_BASE_URL or "https://vorn-bot-nggr.onrender.com").rstrip("/")
    wa_url = f"{base}/app?uid={user.id}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🌀 OPEN APP", web_app=WebAppInfo(url=wa_url))]
    ])
    await context.bot.send_message(
        chat_id=user.id,
        text="🌕 Welcome to the world of the future.\n\nPress the button below to enter the VORN App 👇",
        reply_markup=keyboard
    )
    await context.bot.send_message(chat_id=user.id, text=f"✅ Connected successfully.\n🔗 {wa_url}")

async def btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("OK")

# Admin helpers
async def addcore_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    raw = " ".join(context.args)
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 4:
        await update.message.reply_text("Usage:\n/addcore Title | Reward | Link | Description")
        return
    title, reward, link, desc = parts[0], int(parts[1]), parts[2], parts[3]
    add_task_db("core", title, reward, link, desc, "tg_join", 1)
    await update.message.reply_text(f"✅ Core task added: {title} (+{reward})")

async def adddaily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    raw = update.message.text.replace("/adddaily", "", 1).strip()
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 2:
        await update.message.reply_text("Usage:\n/adddaily Title | Reward | [Link] | [Description]")
        return
    title = parts[0]
    reward = int(parts[1])
    link = parts[2] if len(parts) > 2 else None
    desc = parts[3] if len(parts) > 3 else None
    add_task_db("daily", title, reward, link, desc)
    await update.message.reply_text(f"✅ Daily task added: {title} (+{reward})")

async def cleardaily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    clear_tasks("daily"); await update.message.reply_text("🧹 Daily tasks cleared.")

async def clearcore_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    clear_tasks("core"); await update.message.reply_text("🧹 Core tasks cleared.")

    # =========================
# TASK SYSTEM — Unified API
# =========================

def add_task_advanced(task_type, title, reward_feather, reward_vorn, link=None):
    """Insert task with separate rewards for feathers and vorn."""
    conn = db(); c = conn.cursor()
    # ensure columns exist
    try:
        c.execute("ALTER TABLE tasks ADD COLUMN reward_feather INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE tasks ADD COLUMN reward_vorn REAL DEFAULT 0")
    except Exception:
        pass

    c.execute("""
        INSERT INTO tasks (type, title, reward_feather, reward_vorn, link, created_at, active)
        VALUES (%s, %s, %s, %s, %s, %s, 1)
    """, (task_type, title, int(reward_feather), float(reward_vorn), link, int(time.time())))
    conn.commit(); conn.close()



    conn = db(); c = conn.cursor()
    for sql in [
        "ALTER TABLE tasks ADD COLUMN reward_feather INTEGER DEFAULT 0",
        "ALTER TABLE tasks ADD COLUMN reward_vorn REAL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN vorn_balance REAL DEFAULT 0"
    ]:
        try: c.execute(sql)
        except Exception: pass

    c.execute("""
        SELECT id, type, title, reward_feather, reward_vorn, link
        FROM tasks
        WHERE active = TRUE
        ORDER BY id DESC
    """)

    rows = c.fetchall()

    # 🧠 վերցնենք user-ի արդեն ավարտած տասկերը
    user_done = set()
    if uid:
        date_key = time.strftime("%Y-%m-%d")
        c.execute("SELECT task_id FROM user_tasks WHERE user_id=%s AND date_key=%s", (uid, date_key))
        for r in c.fetchall():
            user_done.add(r[0])

    data = {"main": [], "daily": []}
    for row in rows:
        tid, ttype, title, rf, rv, link = row
        entry = {
            "id": tid,
            "title": title,
            "reward_feather": rf,
            "reward_vorn": rv,
            "link": link or "",
            "completed": tid in user_done
        }
        if ttype not in data:
            data[ttype] = []
        data[ttype].append(entry)

    conn.close()
    return jsonify(data)



# =========================
# Separate Add Commands for MAIN & DAILY
# =========================

async def addmain_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage:
    /addmain Title | FeatherReward | VornReward | [link]"""
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("⛔ Not authorized.")
    raw = update.message.text.replace("/addmain", "", 1).strip()
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 3:
        return await update.message.reply_text(
            "Usage:\n/addmain Title | FeatherReward | VornReward | [link]"
        )
    title = parts[0]
    reward_feather = int(parts[1])
    reward_vorn = float(parts[2])
    link = parts[3] if len(parts) > 3 else None
    add_task_advanced("main", title, reward_feather, reward_vorn, link)
    await update.message.reply_text(
        f"✅ Added MAIN task:\n• {title}\n🪶 {reward_feather} | 🜂 {reward_vorn}"
    )


async def adddaily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage:
    /adddaily Title | FeatherReward | VornReward | [link]"""
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("⛔ Not authorized.")
    raw = update.message.text.replace("/adddaily", "", 1).strip()
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 3:
        return await update.message.reply_text(
            "Usage:\n/adddaily Title | FeatherReward | VornReward | [link]"
        )
    title = parts[0]
    reward_feather = int(parts[1])
    reward_vorn = float(parts[2])
    link = parts[3] if len(parts) > 3 else None
    add_task_advanced("daily", title, reward_feather, reward_vorn, link)
    await update.message.reply_text(
        f"✅ Added DAILY task:\n• {title}\n🪶 {reward_feather} | 🜂 {reward_vorn}"
    )


async def deltask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("⛔ Not authorized.")
    if not context.args:
        return await update.message.reply_text("Usage: /deltask <id>")
    tid = int(context.args[0])
    conn = db(); c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=%s", (tid,))
    conn.commit(); conn.close()
    await update.message.reply_text(f"🗑️ Task {tid} deleted.")


async def listtasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("⛔ Not authorized.")
    conn = db(); c = conn.cursor()
    c.execute("SELECT id, type, title, reward_feather, reward_vorn FROM tasks WHERE active = TRUE ORDER BY id DESC")
    rows = c.fetchall(); conn.close()
    if not rows:
        return await update.message.reply_text("📭 No tasks.")
    msg = "\n".join([f"{tid}. [{t.upper()}] {title} 🪶{rf} 🜂{rv}" for tid, t, title, rf, rv in rows])
    await update.message.reply_text(f"📋 Active Tasks:\n{msg}")




# =========================
# TASK ATTEMPTS SYSTEM (perform → verify)
# =========================

@app_web.route("/api/task_attempt_create", methods=["POST"])
def api_task_attempt_create():
    """
    Create a pending task attempt and return a unique token.
    Used when user clicks 'Perform'.
    """
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    task_id = int(data.get("task_id", 0))
    if not user_id or not task_id:
        return jsonify({"ok": False, "error": "missing user_id or task_id"}), 400

    conn = db(); c = conn.cursor()
    # ensure table exists
    c.execute("""
    CREATE TABLE IF NOT EXISTS task_attempts (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    task_id BIGINT,
    token TEXT,
    status TEXT DEFAULT 'pending',
    created_at BIGINT,
    verified_at BIGINT
    );

    """)
    token = f"T{user_id}_{task_id}_{int(time.time())}"
    c.execute("INSERT INTO task_attempts (user_id, task_id, token, status, created_at) VALUES (%s, %s, %s, 'pending', %s)",
              (user_id, task_id, token, int(time.time())))
    conn.commit(); conn.close()

    return jsonify({"ok": True, "token": token})


# =========================
# Static legal pages (Terms + Privacy)
# =========================
from flask import send_from_directory
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app_web.route('/terms.html')
def serve_terms():
    return send_from_directory(os.path.join(BASE_DIR, 'webapp'), 'terms.html')

@app_web.route('/tiktokxIdyn8EdBKD9JpuXubuRGoh4vXfVZF18.html')
def serve_tiktok_verification():
    return send_from_directory(os.path.join(BASE_DIR, 'webapp'), 'tiktokxIdyn8EdBKD9JpuXubuRGoh4vXfVZF18.html')


@app_web.route('/privacy.html')
def serve_privacy():
    return send_from_directory(os.path.join(BASE_DIR, 'webapp'), 'privacy.html')



@app_web.route("/api/task_attempt_verify", methods=["POST"])
def api_task_attempt_verify():
    """
    Check if user truly completed the task.
    For now: auto-approve for all, later will integrate real checks.
    """
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    task_id = int(data.get("task_id", 0))
    token = data.get("token", "")

    if not user_id or not task_id or not token:
        return jsonify({"ok": False, "error": "missing fields"}), 400

    conn = db(); c = conn.cursor()

    # Check token validity
    c.execute("SELECT id, status FROM task_attempts WHERE user_id=%s AND task_id=%s AND token=%s", (user_id, task_id, token))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"ok": False, "error": "invalid attempt"}), 400
    if row[1] == "verified":
        conn.close()
        return jsonify({"ok": False, "error": "already verified"}), 400

        # ✅ Prevent multiple rewards for the same task
    date_key = time.strftime("%Y-%m-%d")
    c.execute("SELECT 1 FROM user_tasks WHERE user_id=%s AND task_id=%s AND date_key=%s", (user_id, task_id, date_key))
    if c.fetchone():
        conn.close()
        return jsonify({"ok": False, "error": "already_completed"}), 400

    # ✅ Mark as verified
    c.execute("UPDATE task_attempts SET status='verified', verified_at=%s WHERE id=%s", (int(time.time()), row[0]))

    # ✅ Save to user_tasks table (for progress memory)
    c.execute("INSERT INTO user_tasks (user_id, task_id, date_key, completed_at) VALUES (%s, %s, %s, %s)",
              (user_id, task_id, date_key, int(time.time())))

    # ✅ Fetch reward data
    c.execute("SELECT reward_feather, reward_vorn FROM tasks WHERE id=%s", (task_id,))
    task = c.fetchone()
    if not task:
        conn.close()
        return jsonify({"ok": False, "error": "task not found"}), 404

    reward_feather, reward_vorn = task

    # ✅ Add rewards to balance
    try:
        c.execute("ALTER TABLE users ADD COLUMN vorn_balance REAL DEFAULT 0")
    except Exception:
        pass

    c.execute("SELECT balance, vorn_balance FROM users WHERE user_id=%s", (user_id,))
    row_user = c.fetchone()
    balance = (row_user[0] if row_user else 0) + reward_feather
    vorn = (row_user[1] if row_user else 0) + reward_vorn
    c.execute("UPDATE users SET balance=%s, vorn_balance=%s WHERE user_id=%s", (balance, vorn, user_id))

    conn.commit()
    conn.close()

    return jsonify({
        "ok": True,
        "reward_feather": reward_feather,
        "reward_vorn": reward_vorn,
        "new_balance": balance,
        "new_vorn": vorn
    })


# =========================
# VERIFY TASK — Reward distribution
# =========================

@app_web.route("/api/verify_task", methods=["POST"])
def api_verify_task():
    """
    Verify if user completed the task (basic version).
    For now: auto-approve all tasks.
    Later we'll connect Telegram/YouTube/TikTok verification.
    """
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    task_id = int(data.get("task_id", 0))
    if not user_id or not task_id:
        return jsonify({"ok": False, "error": "missing user_id or task_id"}), 400

    conn = db(); c = conn.cursor()

    # ensure vorn_balance exists
    try:
        c.execute("ALTER TABLE users ADD COLUMN vorn_balance REAL DEFAULT 0")
    except Exception:
        pass

    # read task info
    c.execute("SELECT reward_feather, reward_vorn FROM tasks WHERE id=%s AND active = TRUE", (task_id,))
    task = c.fetchone()
    if not task:
        conn.close()
        return jsonify({"ok": False, "error": "task not found"}), 404

    reward_feather, reward_vorn = task

    # check if already done
    date_key = time.strftime("%Y-%m-%d")
    c.execute("SELECT completed_at FROM user_tasks WHERE user_id=%s AND task_id=%s AND date_key=%s", (user_id, task_id, date_key))
    if c.fetchone():
        conn.close()
        return jsonify({"ok": False, "reason": "already_done"})

    # mark as done
    # ✅ PostgreSQL-compatible UPSERT (instead of SQLite INSERT OR REPLACE)
    c.execute("""
    INSERT INTO user_tasks (user_id, task_id, date_key, completed_at)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (user_id, task_id, date_key)
    DO UPDATE SET completed_at = EXCLUDED.completed_at;
    """, (user_id, task_id, date_key, int(time.time())))


    # update balances
    c.execute("SELECT balance, vorn_balance FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone()
    balance = (row[0] if row else 0) + reward_feather
    vorn = (row[1] if row else 0) + reward_vorn
    c.execute("UPDATE users SET balance=%s, vorn_balance=%s WHERE user_id=%s", (balance, vorn, user_id))
    conn.commit(); conn.close()

    return jsonify({
        "ok": True,
        "reward_feather": reward_feather,
        "reward_vorn": reward_vorn,
        "new_balance": balance,
        "new_vorn": vorn
    })


# =====================================================
# 🚀 Telegram Application (Webhook mode, PTB v20)
# =====================================================
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram import MenuButtonWebApp

application = None  # Global

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username)

    base = (PUBLIC_BASE_URL or "https://vorn-bot-nggr.onrender.com").rstrip("/")
    wa_url = f"{base}/app?uid={user.id}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🌀 OPEN APP", web_app=WebAppInfo(url=wa_url))]
    ])
    # Ոչ մի խոսակցություն՝ ուղարկում ենք միայն WebApp-ը
    msg = await context.bot.send_message(
        chat_id=user.id,
        text="🌕 Press the button to enter VORN App 👇",
        reply_markup=keyboard
    )

    # Փին ենք անում, որ սա մնա վերևում
    try:
        await context.bot.pin_chat_message(chat_id=user.id, message_id=msg.message_id)
    except Exception as e:
        print("⚠️ Pin failed:", e)

# User-ի ուղարկած ցանկացած տեքստ ջնջում ենք, որպեսզի չատը «փակ» լինի
async def block_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except Exception:
        pass

async def start_bot_webhook():
    """Build application, add handlers, set webhook and start the app."""
    global application
    print("🤖 Initializing Telegram bot (Webhook Mode)...")

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("addmain", addmain_cmd))
    application.add_handler(CommandHandler("adddaily", adddaily_cmd))
    application.add_handler(CommandHandler("deltask", deltask_cmd))
    application.add_handler(CommandHandler("listtasks", listtasks_cmd))
    application.add_handler(CommandHandler("clearcore", clearcore_cmd))
    application.add_handler(CallbackQueryHandler(btn_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, block_text))

    # Webhook URL
    port = int(os.environ.get("PORT", "10000"))
    webhook_url = f"{PUBLIC_BASE_URL}/webhook"

    # մաքրում ենք հները և դնում նոր webhook
    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook set to {webhook_url}")

    # Կցում ենք default chat menu-ը որպես WebApp կոճակ
    try:
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="🌀 VORN App", web_app=WebAppInfo(url=f"{PUBLIC_BASE_URL}/app"))
        )
        print("✅ Global menu button → WebApp")
    except Exception as e:
        print("⚠️ Failed to set menu button:", e)

    # Սկսում ենք application-ը (loop, jobs, handlers)
    await application.initialize()
    await application.start()
    print("✅ Telegram application started (webhook mode).")



    # --- Run Flask concurrently ---
    from threading import Thread
    def run_flask():
        print("🚀 Flask running in parallel with Telegram webhook.")
        app_web.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)
    Thread(target=run_flask, daemon=True).start()

    # --- Proper Telegram app lifecycle ---
    await application.initialize()
    await application.start()
    await application.updater.start_webhook(listen="0.0.0.0", port=port, url_path="", webhook_url=webhook_url)

    print("✅ Telegram bot started successfully (Webhook mode active).")

    # Keep alive forever
    await asyncio.Event().wait()


from flask import request
import asyncio

@app_web.route("/webhook", methods=["POST"])
def telegram_webhook():
    global application
    if application is None:
        return jsonify({"ok": False, "error": "bot not ready"}), 503

    update_data = request.get_json(force=True, silent=True)
    if not update_data:
        return jsonify({"ok": False, "error": "empty update"}), 400

    try:
        upd = Update.de_json(update_data, application.bot)
        loop = asyncio.get_event_loop()
        loop.create_task(application.process_update(upd))
        return jsonify({"ok": True}), 200
    except RuntimeError:
        # if no loop in this thread (rare), run it quickly in a new loop
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(application.process_update(upd))
            return jsonify({"ok": True}), 200
        except Exception as e:
            print("🔥 Webhook secondary error:", e)
            return jsonify({"ok": False, "error": str(e)}), 500
    except Exception as e:
        print("🔥 Webhook processing error:", e)
        return jsonify({"ok": False, "error": str(e)}), 500



if __name__ == "__main__":
    print("✅ Bot script loaded successfully.")
    try:
        init_db()
        print("✅ Database initialized (PostgreSQL ready).")
    except Exception as e:
        print("⚠️ init_db() failed:", e)

    # 🚀 Telegram bot in a background thread (async)
    def run_bot():
        asyncio.run(start_bot_webhook())
    threading.Thread(target=run_bot, daemon=True).start()

    # 🚀 Flask (Render needs an open port)
    print("🌍 Starting Flask web server (Render port)...")
    port = int(os.environ.get("PORT", "10000"))
    app_web.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)



