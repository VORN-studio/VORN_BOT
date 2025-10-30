# bot.py — VORN Coin (Telegram Bot + Flask WebApp)
# Python 3.10+  |  pip install flask flask-cors python-telegram-bot==20.3

import os
import psycopg2
import time
import threading
from typing import Optional

from flask import Flask, jsonify, send_from_directory, request, redirect, session
from flask_cors import CORS
import asyncio
import requests

# =========================
# Flask Web Server
# =========================
app_web = Flask(__name__, static_folder=None)
CORS(app_web)

@app_web.route("/")
def index():
    return "✅ VORN Bot is online (Render active). Go to /app for interface.", 200

@app_web.route("/<path:anypath>")
def catch_all(anypath):
    return "✅ VORN Bot is running. Unknown path: /" + anypath, 200

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEBAPP_DIR = os.path.join(BASE_DIR, "webapp")  # index.html, app.js, style.css, assets/

@app_web.route("/app")
def app_page():
    return send_from_directory(WEBAPP_DIR, "index.html")

@app_web.route("/webapp/<path:filename>")
def serve_webapp(filename):
    resp = send_from_directory(WEBAPP_DIR, filename)
    if filename.endswith(".mp4"):
        resp.headers["Cache-Control"] = "public, max-age=86400"
        resp.headers["Accept-Ranges"] = "bytes"
        resp.headers["Content-Type"] = "video/mp4"
    elif filename.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        resp.headers["Cache-Control"] = "public, max-age=86400"
    elif filename.endswith((".css", ".js")):
        resp.headers["Cache-Control"] = "no-cache"
    return resp

@app_web.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(WEBAPP_DIR, "assets"), "favicon.ico")

# =========================
# Telegram Bot (PTB v20)
# =========================
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, Bot, MenuButtonWebApp
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

print("✅ Bot script loaded successfully.")

# ---- Config / ENV ----
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var is missing. Set it before running the bot.")

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip() or "https://vorn-bot-nggr.onrender.com"
ADMIN_IDS = {5274439601}

# Referral constants
INVITE_FEATHER_BONUS = int(os.getenv("INVITE_FEATHER_BONUS", "1000"))
INVITE_VORN_BONUS    = float(os.getenv("INVITE_VORN_BONUS", "0.1"))
REFERRAL_CASHBACK_PCT = float(os.getenv("REFERRAL_CASHBACK_PCT", "0.03"))  # 3%

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
    conn.autocommit = True
    c = conn.cursor()
    try:
        c.execute("CREATE SCHEMA IF NOT EXISTS public;")
        c.execute("SET search_path TO public;")
    except Exception as e:
        print("⚠️ DB schema check error:", e)
    return conn

def init_db():
    print("🛠️ Running init_db() ...")
    conn = db(); c = conn.cursor()

    # users
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
        vorn_balance REAL DEFAULT 0,
        last_ref_claim BIGINT DEFAULT 0
    );""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_users_inviter ON users(inviter_id)")

    # tasks
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
        created_at BIGINT,
        reward_feather INTEGER DEFAULT 0,
        reward_vorn REAL DEFAULT 0
    );""")

    # user_tasks
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_tasks (
        user_id BIGINT,
        task_id BIGINT,
        date_key TEXT,
        completed_at BIGINT,
        PRIMARY KEY (user_id, task_id, date_key)
    );""")

    # earnings — 🧾 ցանկացած կրեդիտ՝ լոգով
    c.execute("""
    CREATE TABLE IF NOT EXISTS earnings (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        feather_delta INTEGER DEFAULT 0,
        vorn_delta REAL DEFAULT 0,
        source TEXT,                        -- 'mine','task','vorn_reward','invite_bonus','ref_cashback','click'
        created_at BIGINT NOT NULL
    );""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_earnings_user_time ON earnings(user_id, created_at)")

    conn.commit(); conn.close()
    print("✅ Tables created successfully in PostgreSQL.")

def log_earning(user_id: int, feather_delta: int = 0, vorn_delta: float = 0.0, source: str = ""):
    try:
        conn = db(); c = conn.cursor()
        c.execute("""INSERT INTO earnings (user_id, feather_delta, vorn_delta, source, created_at)
                    VALUES (%s,%s,%s,%s,%s)""",
                  (user_id, int(feather_delta), float(vorn_delta), source, int(time.time())))
        conn.commit(); conn.close()
    except Exception as e:
        print("⚠️ log_earning failed:", e)

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
        if old_inviter is None and inviter_id and inviter_id != user_id:
            c.execute("UPDATE users SET inviter_id=%s WHERE user_id=%s", (inviter_id, user_id))
        c.execute("UPDATE users SET username=%s WHERE user_id=%s", (username, user_id))
    conn.commit(); conn.close()

def get_balance(user_id: int) -> int:
    conn = db(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone(); conn.close()
    return row[0] if row else 0

def update_balance(user_id: int, delta: int, source: str = "manual") -> int:
    conn = db(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone()
    if not row:
        new_balance = int(delta)
        c.execute("INSERT INTO users (user_id, balance) VALUES (%s, %s)", (user_id, new_balance))
    else:
        new_balance = int(row[0]) + int(delta)
        c.execute("UPDATE users SET balance=%s WHERE user_id=%s", (new_balance, user_id))
    conn.commit(); conn.close()
    if delta:
        log_earning(user_id, feather_delta=delta, source=source)
    return new_balance

def add_vorn(user_id: int, vdelta: float, source: str = "manual") -> float:
    conn = db(); c = conn.cursor()
    c.execute("SELECT vorn_balance FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone()
    if not row:
        new_v = float(vdelta)
        c.execute("INSERT INTO users (user_id, vorn_balance) VALUES (%s,%s)", (user_id, new_v))
    else:
        cur = float(row[0] or 0.0)
        new_v = cur + float(vdelta)
        c.execute("UPDATE users SET vorn_balance=%s WHERE user_id=%s", (new_v, user_id))
    conn.commit(); conn.close()
    if vdelta:
        log_earning(user_id, vorn_delta=vdelta, source=source)
    return new_v

def can_mine(user_id: int):
    now = int(time.time())
    conn = db(); c = conn.cursor()
    c.execute("SELECT last_mine FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone()
    last_mine = row[0] if row and row[0] else 0
    conn.close()
    diff = now - last_mine
    if diff >= MINE_COOLDOWN:
        return True, 0
    else:
        return False, MINE_COOLDOWN - diff

def set_last_mine(user_id: int):
    now = int(time.time())
    conn = db(); c = conn.cursor()
    c.execute("UPDATE users SET last_mine=%s, last_reminder_sent=0 WHERE user_id=%s", (now, user_id))
    conn.commit(); conn.close()

# =========================
# Minimal JSON API
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

    new_bal = update_balance(user_id, MINE_REWARD, source="mine")
    set_last_mine(user_id)
    now_ts = int(time.time())
    return jsonify({"ok": True, "reward": MINE_REWARD, "balance": new_bal, "last_mine": now_ts}), 200

@app_web.route("/api/mine_click", methods=["POST"])
def api_mine_click():
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    if not user_id:
        return jsonify({"ok": False, "error": "missing user_id"}), 400
    new_bal = update_balance(user_id, 1, source="click")
    return jsonify({"ok": True, "reward": 1, "balance": new_bal}), 200

@app_web.route("/api/vorn_reward", methods=["POST"])
def api_vorn_reward():
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    amount = float(data.get("amount", 0.02))
    if not user_id:
        return jsonify({"ok": False, "error": "missing user_id"}), 400
    try:
        new_v = add_vorn(user_id, amount, source="vorn_reward")
        print(f"🜂 Added {amount} VORN to {user_id}, new total = {new_v}")
        return jsonify({"ok": True, "vorn_added": amount, "vorn_balance": new_v})
    except Exception as e:
        print("🔥 /api/vorn_reward failed:", e)
        return jsonify({"ok": False, "error": str(e)}), 500

@app_web.route("/api/vorn_exchange", methods=["POST"])
def api_vorn_exchange():
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    if not user_id:
        return jsonify({"ok": False, "error": "missing user_id"}), 400
    COST = 50000
    REWARD = 1.0
    conn = db(); c = conn.cursor()
    c.execute("SELECT balance, vorn_balance FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"ok": False, "error": "user not found"}), 404
    feathers, vorn = row
    if feathers < COST:
        conn.close()
        return jsonify({"ok": False, "error": f"not_enough_feathers"}), 400
    new_feathers = feathers - COST
    new_vorn = vorn + REWARD
    c.execute("UPDATE users SET balance=%s, vorn_balance=%s WHERE user_id=%s", (new_feathers, new_vorn, user_id))
    conn.commit(); conn.close()
    # log both directions as one logical earning for vorn only (feather is spend)
    log_earning(user_id, feather_delta=0, vorn_delta=REWARD, source="vorn_exchange")
    return jsonify({"ok": True, "spent_feathers": COST, "new_balance": new_feathers, "new_vorn": new_vorn})

@app_web.route("/api/tasks")
def api_tasks():
    uid = int(request.args.get("uid", 0))
    conn = db(); c = conn.cursor()
    c.execute("""
        SELECT id, type, title, reward_feather, reward_vorn, link
        FROM tasks
        WHERE active = TRUE
        ORDER BY id DESC
    """)
    rows = c.fetchall()
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

# ----- TASK ATTEMPTS (as before) -----
@app_web.route("/api/task_attempt_create", methods=["POST"])
def api_task_attempt_create():
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    task_id = int(data.get("task_id", 0))
    if not user_id or not task_id:
        return jsonify({"ok": False, "error": "missing user_id or task_id"}), 400
    conn = db(); c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS task_attempts (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        task_id BIGINT,
        token TEXT,
        status TEXT DEFAULT 'pending',
        created_at BIGINT,
        verified_at BIGINT
    );""")
    token = f"T{user_id}_{task_id}_{int(time.time())}"
    c.execute("INSERT INTO task_attempts (user_id, task_id, token, status, created_at) VALUES (%s,%s,%s,'pending',%s)",
              (user_id, task_id, token, int(time.time())))
    conn.commit(); conn.close()
    return jsonify({"ok": True, "token": token})

@app_web.route("/api/task_attempt_verify", methods=["POST"])
def api_task_attempt_verify():
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    task_id = int(data.get("task_id", 0))
    token = data.get("token", "")
    if not user_id or not task_id or not token:
        return jsonify({"ok": False, "error": "missing fields"}), 400
    conn = db(); c = conn.cursor()
    c.execute("SELECT id, status FROM task_attempts WHERE user_id=%s AND task_id=%s AND token=%s",
              (user_id, task_id, token))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"ok": False, "error": "invalid_attempt"}), 400
    if row[1] == "verified":
        conn.close()
        return jsonify({"ok": False, "error": "already_verified"}), 400

    date_key = time.strftime("%Y-%m-%d")
    c.execute("SELECT 1 FROM user_tasks WHERE user_id=%s AND task_id=%s AND date_key=%s",
              (user_id, task_id, date_key))
    if c.fetchone():
        conn.close()
        return jsonify({"ok": False, "error": "already_completed"}), 400

    c.execute("UPDATE task_attempts SET status='verified', verified_at=%s WHERE id=%s",
              (int(time.time()), row[0]))
    c.execute("INSERT INTO user_tasks (user_id, task_id, date_key, completed_at) VALUES (%s,%s,%s,%s)",
              (user_id, task_id, date_key, int(time.time())))
    c.execute("SELECT reward_feather, reward_vorn FROM tasks WHERE id=%s", (task_id,))
    task = c.fetchone()
    if not task:
        conn.close()
        return jsonify({"ok": False, "error": "task_not_found"}), 404
    reward_feather, reward_vorn = task

    # credit rewards
    # feathers
    if reward_feather:
        c.execute("UPDATE users SET balance=COALESCE(balance,0)+%s WHERE user_id=%s", (reward_feather, user_id))
        log_earning(user_id, feather_delta=reward_feather, source="task")
    # vorn
    if reward_vorn:
        c.execute("UPDATE users SET vorn_balance=COALESCE(vorn_balance,0)+%s WHERE user_id=%s", (reward_vorn, user_id))
        log_earning(user_id, vorn_delta=reward_vorn, source="task")
    # read new
    c.execute("SELECT balance, vorn_balance FROM users WHERE user_id=%s", (user_id,))
    row_user = c.fetchone()
    balance = row_user[0] or 0
    vorn = row_user[1] or 0.0
    conn.commit(); conn.close()
    return jsonify({"ok": True, "reward_feather": reward_feather, "reward_vorn": reward_vorn,
                    "new_balance": balance, "new_vorn": vorn})

# =========================
# VERIFY TASK (simple)
# =========================
@app_web.route("/api/verify_task", methods=["POST"])
def api_verify_task():
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    task_id = int(data.get("task_id", 0))
    if not user_id or not task_id:
        return jsonify({"ok": False, "error": "missing user_id or task_id"}), 400
    conn = db(); c = conn.cursor()
    c.execute("SELECT reward_feather, reward_vorn FROM tasks WHERE id=%s AND active=TRUE", (task_id,))
    task = c.fetchone()
    if not task:
        conn.close(); return jsonify({"ok": False, "error": "task_not_found"}), 404
    reward_feather, reward_vorn = task
    date_key = time.strftime("%Y-%m-%d")
    c.execute("""INSERT INTO user_tasks (user_id, task_id, date_key, completed_at)
                 VALUES (%s,%s,%s,%s)
                 ON CONFLICT (user_id, task_id, date_key)
                 DO UPDATE SET completed_at = EXCLUDED.completed_at""",
              (user_id, task_id, date_key, int(time.time())))
    # credit
    if reward_feather:
        c.execute("UPDATE users SET balance=COALESCE(balance,0)+%s WHERE user_id=%s", (reward_feather, user_id))
        log_earning(user_id, feather_delta=reward_feather, source="task")
    if reward_vorn:
        c.execute("UPDATE users SET vorn_balance=COALESCE(vorn_balance,0)+%s WHERE user_id=%s", (reward_vorn, user_id))
        log_earning(user_id, vorn_delta=reward_vorn, source="task")
    c.execute("SELECT balance, vorn_balance FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone()
    conn.commit(); conn.close()
    return jsonify({"ok": True, "reward_feather": reward_feather, "reward_vorn": reward_vorn,
                    "new_balance": row[0] or 0, "new_vorn": row[1] or 0.0})

# =========================
# 📣 REFERRAL API
# =========================

def _referral_ids(inviter_id: int):
    conn = db(); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE inviter_id=%s", (inviter_id,))
    ids = [r[0] for r in c.fetchall()]
    conn.close()
    return ids

@app_web.route("/api/referrals")
def api_referrals():
    uid = int(request.args.get("uid", 0))
    if not uid:
        return jsonify({"ok": False, "error": "missing uid"}), 400
    ids = _referral_ids(uid)
    data = []
    if ids:
        conn = db(); c = conn.cursor()
        c.execute("""SELECT user_id, username, COALESCE(balance,0), COALESCE(vorn_balance,0)
                     FROM users WHERE user_id = ANY(%s)""", (ids,))
        rows = c.fetchall()
        conn.close()
        # sort by total feathers desc (top list)
        rows.sort(key=lambda x: (x[2], x[3]), reverse=True)
        for i, r in enumerate(rows, start=1):
            data.append({
                "rank": i,
                "user_id": r[0],
                "username": r[1] or f"User{r[0]}",
                "feathers": int(r[2]),
                "vorn": float(r[3])
            })
    return jsonify({"ok": True, "list": data})

@app_web.route("/api/referrals/preview")
def api_referrals_preview():
    uid = int(request.args.get("uid", 0))
    if not uid:
        return jsonify({"ok": False, "error": "missing uid"}), 400
    conn = db(); c = conn.cursor()
    c.execute("SELECT last_ref_claim FROM users WHERE user_id=%s", (uid,))
    row = c.fetchone()
    last_ts = int(row[0] or 0)
    refs = _referral_ids(uid)
    feather_total = 0
    vorn_total = 0.0
    if refs:
        # sum positive deltas since last claim
        c.execute("""
            SELECT SUM(GREATEST(feather_delta,0)), SUM(GREATEST(vorn_delta,0))
            FROM earnings
            WHERE user_id = ANY(%s) AND created_at > %s
        """, (refs, last_ts))
        sums = c.fetchone()
        if sums and (sums[0] or sums[1]):
            feather_total = int(sums[0] or 0)
            vorn_total = float(sums[1] or 0.0)
    conn.close()
    cashback_feathers = int(feather_total * REFERRAL_CASHBACK_PCT)
    cashback_vorn = round(vorn_total * REFERRAL_CASHBACK_PCT, 6)
    return jsonify({"ok": True,
                    "from_ts": last_ts,
                    "base_feathers": feather_total,
                    "base_vorn": vorn_total,
                    "cashback_feathers": cashback_feathers,
                    "cashback_vorn": cashback_vorn})

@app_web.route("/api/referrals/claim", methods=["POST"])
def api_referrals_claim():
    data = request.get_json(force=True, silent=True) or {}
    uid = int(data.get("uid", 0))
    if not uid:
        return jsonify({"ok": False, "error": "missing uid"}), 400
    now = int(time.time())
    conn = db(); c = conn.cursor()
    c.execute("SELECT last_ref_claim FROM users WHERE user_id=%s", (uid,))
    row = c.fetchone()
    last_ts = int(row[0] or 0)
    refs = _referral_ids(uid)
    feather_total = 0
    vorn_total = 0.0
    if refs:
        c.execute("""
            SELECT SUM(GREATEST(feather_delta,0)), SUM(GREATEST(vorn_delta,0))
            FROM earnings
            WHERE user_id = ANY(%s) AND created_at > %s
        """, (refs, last_ts))
        sums = c.fetchone()
        if sums and (sums[0] or sums[1]):
            feather_total = int(sums[0] or 0)
            vorn_total = float(sums[1] or 0.0)

    cashback_feathers = int(feather_total * REFERRAL_CASHBACK_PCT)
    cashback_vorn = round(vorn_total * REFERRAL_CASHBACK_PCT, 6)

    # nothing to claim
    if cashback_feathers <= 0 and cashback_vorn <= 0:
        conn.close()
        return jsonify({"ok": False, "error": "nothing_to_claim"})

    # credit inviter
    if cashback_feathers:
        c.execute("UPDATE users SET balance=COALESCE(balance,0)+%s WHERE user_id=%s", (cashback_feathers, uid))
        log_earning(uid, feather_delta=cashback_feathers, source="ref_cashback")
    if cashback_vorn:
        c.execute("UPDATE users SET vorn_balance=COALESCE(vorn_balance,0)+%s WHERE user_id=%s", (cashback_vorn, uid))
        log_earning(uid, vorn_delta=cashback_vorn, source="ref_cashback")

    c.execute("UPDATE users SET last_ref_claim=%s WHERE user_id=%s", (now, uid))
    # read new balances
    c.execute("SELECT balance, vorn_balance FROM users WHERE user_id=%s", (uid,))
    balrow = c.fetchone()
    conn.commit(); conn.close()

    return jsonify({"ok": True,
                    "cashback_feathers": cashback_feathers,
                    "cashback_vorn": cashback_vorn,
                    "new_balance": int(balrow[0] or 0),
                    "new_vorn": float(balrow[1] or 0.0)})

# =========================
# Static legal pages
# =========================
@app_web.route('/terms.html')
def serve_terms():
    return send_from_directory(os.path.join(BASE_DIR, 'webapp'), 'terms.html')

@app_web.route('/tiktokxIdyn8EdBKD9JpuXubuRGoh4vXfVZF18.html')
def serve_tiktok_verification_html():
    return send_from_directory(os.path.join(BASE_DIR, 'webapp'), 'tiktokxIdyn8EdBKD9JpuXubuRGoh4vXfVZF18.html')

@app_web.route('/privacy.html')
def serve_privacy():
    return send_from_directory(os.path.join(BASE_DIR, 'webapp'), 'privacy.html')

@app_web.route("/tiktokxIdyn8EdBKD9JpuXubuRGoh4vXfVZF18.txt")
def serve_tiktok_verif_standard():
    return send_from_directory(BASE_DIR, "tiktokxIdyn8EdBKD9JpuXubuRGoh4vXfVZF18.txt")

@app_web.route("/tiktok-developers-site-verification.txt")
def tiktok_verification_file():
    return "tiktok-developers-site-verification=xIdyn8EdBKD9JpuXubuRGoh4vXfVZF18", 200, {
        "Content-Type": "text/plain; charset=utf-8"
    }

# =========================
# Telegram handlers
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
    user = update.effective_user
    inviter_id = None
    # capture ref if present
    if update.message and update.message.text:
        inviter_id = parse_start_payload(update.message.text)
        if inviter_id == user.id:
            inviter_id = None  # prevent self-ref
    ensure_user(user.id, user.username, inviter_id=inviter_id)

    # one-time invite bonus to inviter
    if inviter_id:
        try:
            # check if inviter already got bonus for this user
            conn = db(); c = conn.cursor()
            c.execute("""SELECT 1 FROM earnings
                         WHERE user_id=%s AND source='invite_bonus' AND created_at > %s""",
                      (inviter_id, 0))
            # we still need to ensure per-invite uniqueness:
            c.execute("""SELECT 1 FROM earnings
                         WHERE user_id=%s AND source=%s""", (inviter_id, f"invite_bonus:{user.id}"))
            got = c.fetchone()
            if not got:
                if INVITE_FEATHER_BONUS:
                    c.execute("UPDATE users SET balance=COALESCE(balance,0)+%s WHERE user_id=%s",
                              (INVITE_FEATHER_BONUS, inviter_id))
                if INVITE_VORN_BONUS:
                    c.execute("UPDATE users SET vorn_balance=COALESCE(vorn_balance,0)+%s WHERE user_id=%s",
                              (INVITE_VORN_BONUS, inviter_id))
                conn.commit(); conn.close()
                # log with unique source tag to avoid duplicates
                log_earning(inviter_id,
                            feather_delta=INVITE_FEATHER_BONUS,
                            vorn_delta=INVITE_VORN_BONUS,
                            source=f"invite_bonus:{user.id}")
        except Exception as e:
            print("⚠️ invite bonus failed:", e)

    base = PUBLIC_BASE_URL.rstrip("/")
    wa_url = f"{base}/app?uid={user.id}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🌀 OPEN APP", web_app=WebAppInfo(url=wa_url))]
    ])
    msg = await context.bot.send_message(
        chat_id=user.id,
        text="🌕 Press the button to enter VORN App 👇",
        reply_markup=keyboard
    )
    try:
        await context.bot.pin_chat_message(chat_id=user.id, message_id=msg.message_id)
    except Exception:
        pass

async def btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("OK")

async def block_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.delete()
    except Exception:
        pass

async def addmain_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("⛔ Not authorized.")
    raw = update.message.text.replace("/addmain", "", 1).strip()
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 3:
        return await update.message.reply_text("Usage:\n/addmain Title | FeatherReward | VornReward | [link]")
    title = parts[0]
    reward_feather = int(parts[1])
    reward_vorn = float(parts[2])
    link = parts[3] if len(parts) > 3 else None
    conn = db(); c = conn.cursor()
    c.execute("""INSERT INTO tasks (type, title, reward_feather, reward_vorn, link, created_at, active)
                 VALUES ('main', %s, %s, %s, %s, %s, TRUE)""",
              (title, reward_feather, reward_vorn, link, int(time.time())))
    conn.commit(); conn.close()
    await update.message.reply_text(f"✅ Added MAIN task:\n• {title}\n🪶 {reward_feather} | 🜂 {reward_vorn}")

async def adddaily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("⛔ Not authorized.")
    raw = update.message.text.replace("/adddaily", "", 1).strip()
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 3:
        return await update.message.reply_text("Usage:\n/adddaily Title | FeatherReward | VornReward | [link]")
    title = parts[0]
    reward_feather = int(parts[1])
    reward_vorn = float(parts[2])
    link = parts[3] if len(parts) > 3 else None
    conn = db(); c = conn.cursor()
    c.execute("""INSERT INTO tasks (type, title, reward_feather, reward_vorn, link, created_at, active)
                 VALUES ('daily', %s, %s, %s, %s, %s, TRUE)""",
              (title, reward_feather, reward_vorn, link, int(time.time())))
    conn.commit(); conn.close()
    await update.message.reply_text(f"✅ Added DAILY task:\n• {title}\n🪶 {reward_feather} | 🜂 {reward_vorn}")

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
    c.execute("SELECT id, type, title, reward_feather, reward_vorn FROM tasks WHERE active=TRUE ORDER BY id DESC")
    rows = c.fetchall(); conn.close()
    if not rows:
        return await update.message.reply_text("📭 No tasks.")
    msg = "\n".join([f"{tid}. [{t.upper()}] {title} 🪶{rf} 🜂{rv}" for tid, t, title, rf, rv in rows])
    await update.message.reply_text(f"📋 Active Tasks:\n{msg}")

application = None

async def start_bot_webhook():
    global application
    print("🤖 Initializing Telegram bot (Webhook Mode)...")
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("addmain", addmain_cmd))
    application.add_handler(CommandHandler("adddaily", adddaily_cmd))
    application.add_handler(CommandHandler("deltask", deltask_cmd))
    application.add_handler(CommandHandler("listtasks", listtasks_cmd))
    application.add_handler(CallbackQueryHandler(btn_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, block_text))

    port = int(os.environ.get("PORT", "10000"))
    webhook_url = f"{PUBLIC_BASE_URL}/webhook"

    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(url=webhook_url)
    try:
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="🌀 VORN App", web_app=WebAppInfo(url=f"{PUBLIC_BASE_URL}/app"))
        )
    except Exception as e:
        print("⚠️ Failed to set menu button:", e)

    await application.initialize()
    await application.start()

    # Run Flask in parallel
    from threading import Thread
    def run_flask():
        print("🚀 Flask running in parallel with Telegram webhook.")
        app_web.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)
    Thread(target=run_flask, daemon=True).start()

    print("✅ Telegram bot started successfully (Webhook mode active).")
    await asyncio.Event().wait()

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
    except Exception as e:
        print("🔥 Webhook processing error:", e)
        return jsonify({"ok": False, "error": str(e)}), 500

# =========================
# 🌐 GOOGLE AUTH (YouTube)
# =========================
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = f"{PUBLIC_BASE_URL}/auth/google/callback"
GOOGLE_AUTH_SCOPE = "https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/userinfo.profile"

@app_web.route("/auth/google")
def google_auth():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": GOOGLE_AUTH_SCOPE,
        "access_type": "offline",
        "prompt": "consent"
    }
    qs = "&".join([f"{k}={v}" for k, v in params.items()])
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?{qs}")

@app_web.route("/auth/google/callback")
def google_callback():
    code = request.args.get("code")
    if not code:
        return "❌ Missing code", 400
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    token_resp = requests.post("https://oauth2.googleapis.com/token", data=token_data)
    tokens = token_resp.json()
    access_token = tokens.get("access_token")
    if not access_token:
        return f"❌ Token exchange failed: {tokens}", 400
    headers = {"Authorization": f"Bearer {access_token}"}
    yt_resp = requests.get("https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true", headers=headers)
    data = yt_resp.json()
    return jsonify({"ok": True, "youtube": data})

if __name__ == "__main__":
    print("✅ Bot script loaded successfully.")
    try:
        init_db()
        print("✅ Database initialized (PostgreSQL ready).")
    except Exception as e:
        print("⚠️ init_db() failed:", e)
    def run_bot():
        asyncio.run(start_bot_webhook())
    threading.Thread(target=run_bot, daemon=True).start()
    print("🌍 Starting Flask web server (Render port)...")
    port = int(os.environ.get("PORT", "10000"))
    app_web.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)
