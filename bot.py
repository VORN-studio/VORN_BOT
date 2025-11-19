# bot.py — VORN Coin (Telegram Bot + Flask WebApp)
# Python 3.10+  |  pip install flask flask-cors python-telegram-bot==20.3

import os
import time
import threading
from typing import Optional

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from support_bot import start_support_runtime, enqueue_support_update


last_exchange_ts = {}
EXCHANGE_GUARD_WINDOW = 5  # sec


# -------------------------------
# MULTILINGUAL REFERRAL TEXTS
# -------------------------------
INVITE_TEXTS = {
    "en": "🌕 Confidential Access — VORN\n\nA hidden route has unlocked.\nThis entry is not public.\n\nYour encrypted gate:\n{ref}\n\n🜂 If you enter, the system will register you instantly.",
    "ru": "🌕 Конфиденциальный доступ — VORN\n\nСкрытый маршрут был открыт.\nЭтот вход не является публичным.\n\nВаш зашифрованный проход:\n{ref}\n\n🜂 Если войдёте, система зарегистрирует вас мгновенно.",
    "hy": "🌕 Գաղտնի Մուտք — VORN\n\nԹաքնված ուղին բացվել է։\nԱյս մուտքը հանրային չէ։\n\nՔո կոդավորված դարպասը՝\n{ref}\n\n🜂 Եթե մուտք գործես, համակարգը կգրանցի քեզ անմիջապես.",
    "fr": "🌕 Accès Confidentiel — VORN\n\nUn passage caché s’est ouvert.\nCet accès n’est pas public.\n\nVotre porte chiffrée :\n{ref}\n\n🜂 Si vous entrez, le système vous enregistrera instantanément.",
    "es": "🌕 Acceso Confidencial — VORN\n\nUna ruta oculta se ha desbloqueado.\nEsta entrada no es pública.\n\nTu puerta cifrada:\n{ref}\n\n🜂 Si entras, el sistema te registrará al instante.",
    "de": "🌕 Vertraulicher Zugang — VORN\n\nEin versteckter Pfad wurde freigeschaltet.\nDieser Zugang ist nicht öffentlich.\n\nDein verschlüsseltes Tor:\n{ref}\n\n🜂 Wenn du eintrittst, registriert dich das System sofort.",
    "it": "🌕 Accesso Confidenziale — VORN\n\nUn percorso nascosto è stato sbloccato.\nQuesto ingresso non è pubblico.\n\nIl tuo varco criptato:\n{ref}\n\n🜂 Se entri, il sistema ti registrerà all’istante.",
    "tr": "🌕 Gizli Erişim — VORN\n\nGizli bir yol açıldı.\nBu giriş herkese açık değildir.\n\nŞifreli geçidin:\n{ref}\n\n🜂 Girersen, sistem seni anında kaydeder.",
    "fa": "🌕 دسترسی محرمانه — VORN\n\nیک مسیر پنهان باز شده است.\nاین ورودی عمومی نیست.\n\nدروازه رمزگذاری‌شده شما:\n{ref}\n\n🜂 اگر وارد شوید، سیستم فوراً شما را ثبت می‌کند.",
    "ar": "🌕 وصول سري — VORN\n\nتم فتح مسار مخفي.\nهذا المدخل غير علني.\n\nبوابتك المشفرة:\n{ref}\n\n🜂 إذا دخلت، سيسجّلك النظام فورًا.",
    "zh": "🌕 机密入口 — VORN\n\n一条隐藏的通道已开启。\n此入口不对公众开放。\n\n你的加密入口：\n{ref}\n\n🜂 进入后，系统会立即登记你。",
    "ja": "🌕 機密アクセス — VORN\n\n隠されたルートが解放されました。\nこの入口は公開されていません。\n\nあなたの暗号化ゲート：\n{ref}\n\n🜂 入れば、システムが即座に登録します。",
    "ko": "🌕 기밀 접속 — VORN\n\n숨겨진 경로가 열렸습니다.\n이 입구는 공개되어 있지 않습니다.\n\n당신의 암호화된 게이트:\n{ref}\n\n🜂 들어오면 시스템이 즉시 등록합니다.",
    "hi": "🌕 गोपनीय प्रवेश — VORN\n\nएक छिपा मार्ग खुल गया है।\nयह प्रवेश सार्वजनिक नहीं है।\n\nआपका एन्क्रिप्टेड द्वार:\n{ref}\n\n🜂 प्रवेश करते ही सिस्टम तुरंत रजिस्टर करेगा.",
    "pt": "🌕 Acesso Confidencial — VORN\n\nUma rota oculta foi desbloqueada.\nEsta entrada não é pública.\n\nSeu portão criptografado:\n{ref}\n\n🜂 Se entrar, o sistema o registrará instantaneamente.",
    "el": "🌕 Απόρρητη Πρόσβαση — VORN\n\nΈνα κρυφό μονοπάτι άνοιξε.\nΑυτή η είσοδος δεν είναι δημόσια.\n\nΗ κρυπτογραφημένη πύλη σου:\n{ref}\n\n🜂 Αν μπεις, το σύστημα θα σε καταγράψει άμεσα.",
    "pl": "🌕 Poufny Dostęp — VORN\n\nUkryta ścieżka została odblokowana.\nTo wejście nie jest publiczne.\n\nTwoja zaszyfrowana brama:\n{ref}\n\n🜂 Jeśli wejdziesz, system natychmiast cię zarejestruje.",
    "nl": "🌕 Vertrouwelijke Toegang — VORN\n\nEen verborgen route is geopend.\nDeze toegang is niet openbaar.\n\nJouw versleutelde poort:\n{ref}\n\n🜂 Als je binnenkomt, registreert het systeem je direct.",
    "sv": "🌕 Konfidentiell Åtkomst — VORN\n\nEn dold väg har låsts upp.\nDenna ingång är inte offentlig.\n\nDin krypterade port:\n{ref}\n\n🜂 Om du går in registrerar systemet dig direkt.",
    "ro": "🌕 Acces Confidențial — VORN\n\nO rută ascunsă a fost deblocată.\nAceastă intrare nu este publică.\n\nPoarta ta criptată:\n{ref}\n\n🜂 Dacă intri, sistemul te va înregistra instant.",
    "hu": "🌕 Bizalmas Hozzáférés — VORN\n\nEgy rejtett út megnyílt.\nEz a belépés nem nyilvános.\n\nA titkosított kapud:\n{ref}\n\n🜂 Ha belépsz, a rendszer azonnal regisztrál.",
    "cs": "🌕 Důvěrný Přístup — VORN\n\nSkrytá cesta byla odemčena.\nTento vstup není veřejný.\n\nTvá šifrovaná brána:\n{ref}\n\n🜂 Pokud vstoupíš, systém tě okamžitě zaregistruje.",
    "uk": "🌕 Конфіденційний Доступ — VORN\n\nПрихований маршрут відкрито.\nЦей вхід не є публічним.\n\nТвій зашифрований прохід:\n{ref}\n\n🜂 Якщо увійдеш, система зареєструє тебе миттєво.",
    "az": "🌕 Konfidensial Giriş — VORN\n\nGizli bir yol açılıb.\nBu giriş ictimai deyil.\n\nŞifrələnmiş keçidin:\n{ref}\n\n🜂 Daxil olsan, sistem səni dərhal qeyd edəcək.",
    "ka": "🌕 კონფიდენციალური წვდომა — VORN\n\nდამალული ბილიკი გაიხსნა.\nეს შესასვლელი საჯარო არ არის.\n\nშენი დაშიფრული კარი:\n{ref}\n\n🜂 თუ შეხვიდე, სისტემა მყისიერად დაგარეგისტრირებს."
}

INVITE_BUTTONS = {
    "en": "📩 Share with a friend",
    "ru": "📩 Поделиться с другом",
    "hy": "📩 Ուղարկել ընկերոջը",
    "fr": "📩 Partager avec un ami",
    "es": "📩 Compartir con un amigo",
    "de": "📩 Mit einem Freund teilen",
    "it": "📩 Condividi con un amico",
    "tr": "📩 Bir arkadaşla paylaş",
    "fa": "📩 ارسال برای دوست",
    "ar": "📩 شارك مع صديق",
    "zh": "📩 与朋友分享",
    "ja": "📩 友達に送る",
    "ko": "📩 친구에게 보내기",
    "hi": "📩 दोस्त को भेजें",
    "pt": "📩 Compartilhar com amigo",
    "el": "📩 Μοιράσου με φίλο",
    "pl": "📩 Udostępnij znajomemu",
    "nl": "📩 Delen met een vriend",
    "sv": "📩 Dela med en vän",
    "ro": "📩 Trimite unui prieten",
    "hu": "📩 Megosztás egy baráttal",
    "cs": "📩 Sdílet s přítelem",
    "uk": "📩 Поділитися з другом",
    "az": "📩 Dostuna göndər",
    "ka": "📩 გაუზიარე მეგობარს"
}



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

from flask import send_from_directory

@app_web.route('/googleac678a462577a462.html')
def google_verification():
    return send_from_directory('.', 'googleac678a462577a462.html')


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
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    Bot,
    InputTextMessageContent,      # ✅ Ավելացրու
    InlineQueryResultArticle      # ✅ Ավելացրու
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
    InlineQueryHandler            # ✅ Ավելացրու
)

print("✅ Bot script loaded successfully.")

# ---- Config / ENV ----
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var is missing. Set it before running the bot.")

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip()
if not PUBLIC_BASE_URL:
    PUBLIC_BASE_URL = "https://vorn-bot-nggr.onrender.com"

BOT_USERNAME = os.getenv("BOT_USERNAME", "VORNCoinbot").lstrip("@")
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

import psycopg2
from psycopg2 import pool  # ✅ սա պետք է լինի այստեղ, ոչ թե հետո

# 🧠 GLOBAL DB POOL
_db_pool = None

def db():
    """
    Creates or reuses PostgreSQL connection pool.
    Fixes psycopg2.pool.PoolError and NoneType issues.
    """
    global _db_pool

    try:
        # եթե pool-ը դեռ չկա — ստեղծում ենք
        if _db_pool is None:
            _db_pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=8,
                dsn=DATABASE_URL,
                sslmode="require"
            )
            print("🧩 PostgreSQL pool initialized (max 8 connections).")

        # փորձում ենք վերցնել կապ pool-ից
        try:
            conn = _db_pool.getconn()
        except Exception as e:
            print("⚠️ Pool exhausted, using temporary direct connection:", e)
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")

        conn.autocommit = True
        return conn

    except Exception as e:
        print("🔥 DB connection failed:", e)
        raise e


def release_db(conn):
    """
    Safely return connection to the pool.
    """
    global _db_pool
    try:
        if _db_pool:
            _db_pool.putconn(conn)
        else:
            conn.close()
    except Exception as e:
        print("⚠️ release_db error:", e)






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
    vorn_balance NUMERIC(20,6) DEFAULT 0
)
""")

    c.execute("""
    ALTER TABLE users
    ALTER COLUMN vorn_balance TYPE NUMERIC(20,6)
    USING COALESCE(vorn_balance, 0)::NUMERIC(20,6)
""")

    c.execute("""
    ALTER TABLE users
    ALTER COLUMN vorn_balance SET DEFAULT 0
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

    c.execute("""
        CREATE TABLE IF NOT EXISTS referral_history AS
        SELECT * FROM referral_earnings WHERE false;
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

    c.execute("""
CREATE TABLE IF NOT EXISTS ref_progress (
    user_id BIGINT PRIMARY KEY,
    level INTEGER DEFAULT 1,
    carried_invites INTEGER DEFAULT 0,
    updated_at BIGINT
)
""")


        # --- Referral earnings table ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS referral_earnings (
        id SERIAL PRIMARY KEY,
        inviter_id BIGINT,
        referred_id BIGINT,
        amount_feathers INTEGER DEFAULT 0,
        amount_vorn REAL DEFAULT 0,
        created_at BIGINT
    )
    """)


    for sql in alters:
        try: c.execute(sql)
        except Exception: pass

        conn.commit()
    release_db(conn)
    print("✅ Tables created successfully in PostgreSQL.")


    # ---- DB helper to always return connections to the pool ----
def close_conn(conn, cursor=None, commit=False):
    try:
        if cursor is not None:
            try:
                if commit:
                    conn.commit()
                else:
                    conn.rollback()
            except Exception:
                pass
            try:
                cursor.close()
            except Exception:
                pass
    finally:
        try:
            _db_pool.putconn(conn)
        except Exception:
            pass


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
        conn.commit(); release_db(conn)
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
        conn.commit(); release_db(conn)
    except Exception:
        pass

    

def ensure_user(user_id: int, username: Optional[str], inviter_id: Optional[int] = None):
    # ❌ Block self-referral at the gate
    if inviter_id == user_id:
        inviter_id = None

    conn = db(); c = conn.cursor()
    c.execute("SELECT user_id, inviter_id FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone()

    if row is None:
        # First time we ever see this user → allow inviter_id (if provided)
        c.execute("""
            INSERT INTO users (user_id, username, balance, last_mine, language, intro_seen, last_reminder_sent, inviter_id)
            VALUES (%s, %s, 0, 0, 'en', 0, 0, %s)
        """, (user_id, username, inviter_id))
    else:
        # Already known user → NEVER change inviter_id (one-time rule)
        c.execute("UPDATE users SET username=%s WHERE user_id=%s", (username, user_id))

    # ✅ Ստուգում ենք՝ արդյոք inviter-ը անցել է նոր լվլ
    if inviter_id:
        check_ref_level_progress(inviter_id)

    conn.commit()
    release_db(conn)

def check_ref_level_progress(inviter_id: int):
    """
    Ստուգում է՝ արդյոք inviter-ը անցել է նոր level, և եթե այո՝ տալիս է համապատասխան բոնուսը։
    """
    if not inviter_id:
        return

    try:
        conn = db()
        c = conn.cursor()

        # Հրավիրածների ընդհանուր քանակը
        c.execute("SELECT COUNT(*) FROM users WHERE inviter_id=%s", (inviter_id,))
        total_invited = c.fetchone()[0] or 0

        # Նախորդ մակարդակը ref_progress աղյուսակից
        c.execute("SELECT level FROM ref_progress WHERE user_id=%s", (inviter_id,))
        row = c.fetchone()
        if not row:
            c.execute(
                "INSERT INTO ref_progress (user_id, level, carried_invites, updated_at) VALUES (%s, %s, %s, %s)",
                (inviter_id, 1, 0, int(time.time()))
            )
            current_level = 1
        else:
            current_level = row[0]

        # Հաջորդ մակարդակի շեմը
        next_idx = current_level  # 👉 վերցնում ենք հաջորդ լեվլի ինդեքսը
        if next_idx >= len(REF_LEVELS):
            return  # արդեն հասել է առավելագույն մակարդակին

        need = REF_LEVELS[next_idx]["need"]


        # Եթե հավաքել է բավարար հրավիրվածներ՝ անցնում է հաջորդ մակարդակ
        if total_invited >= need:
            new_level = current_level + 1
            feathers = REF_LEVELS[next_idx]["feathers"]
            vorn = REF_LEVELS[next_idx]["vorn"]

            # Թարմացնում ենք օգտատիրոջ բալանսը
            c.execute("SELECT balance, vorn_balance FROM users WHERE user_id=%s", (inviter_id,))
            row_u = c.fetchone() or (0, 0.0)
            new_balance = (row_u[0] or 0) + feathers
            new_vorn = (row_u[1] or 0.0) + vorn
            c.execute(
                "UPDATE users SET balance=%s, vorn_balance=%s WHERE user_id=%s",
                (new_balance, new_vorn, inviter_id)
            )

            # Թարմացնում ենք ref_progress աղյուսակը
            c.execute(
                "UPDATE ref_progress SET level=%s, carried_invites=0, updated_at=%s WHERE user_id=%s",
                (new_level, int(time.time()), inviter_id)
            )

            conn.commit()
            print(f"🎉 Referral Level Up → User {inviter_id} reached level {new_level} and earned {feathers}🪶 + {vorn}🜂")
        release_db(conn)
    except Exception as e:
        print("🔥 check_ref_level_progress error:", e)
        try:
            release_db(conn)
        except Exception:
            pass


def get_balance(user_id: int) -> int:
    conn = db(); c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone()
    release_db(conn)
    return row[0] if row else 0

def add_referral_bonus(referred_id: int, reward_feathers: int = 0, reward_vorn: float = 0.0):
    print(f"🎯 add_referral_bonus called for referred_id={referred_id}, reward_feathers={reward_feathers}, reward_vorn={reward_vorn}")
    """
    ՍԱ ՔԱՅԼԱԹՈՂ — ՈՉԻՆՉ ՉԵՆՔ ԱՆԵԼԻ ԲԱՑԻ ԿՈՒՏԱԿԵԼՈՒՑ.
    Գ੍ਰանցում ենք 3% referral_earnings աղյուսակում, իսկ գումարելը կլինի միայն claim-ով:
    """
    conn = db(); c = conn.cursor()
    c.execute("SELECT inviter_id FROM users WHERE user_id=%s", (referred_id,))
    row = c.fetchone()
    if not row or not row[0]:
        release_db(conn)
        return
    inviter_id = row[0]

    bonus_feathers = int(reward_feathers * 0.03)
    bonus_vorn = float(reward_vorn * 0.03)

    # ՄԻԱՅՆ կուտակում ենք
    c.execute("""
        INSERT INTO referral_earnings (inviter_id, referred_id, amount_feathers, amount_vorn, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (inviter_id, referred_id, bonus_feathers, bonus_vorn, int(time.time())))

    conn.commit(); release_db(conn)

def get_ref_level_state(uid: int):
    conn = db(); c = conn.cursor()
    c.execute("SELECT level, carried_invites FROM ref_progress WHERE user_id=%s", (uid,))
    row = c.fetchone()
    if not row:
        level, carry = 1, 0
        c.execute("INSERT INTO ref_progress (user_id, level, carried_invites, updated_at) VALUES (%s, %s, %s, %s)",
                  (uid, level, carry, int(time.time())))
        conn.commit()
    else:
        level, carry = row

    # քանի հոգի է lifetime հրավիրել
    c.execute("SELECT COUNT(*) FROM users WHERE inviter_id=%s", (uid,))
    total_invited = c.fetchone()[0] or 0

    idx = min(level, len(REF_LEVELS)) - 1
    need = REF_LEVELS[idx]["need"] if idx >= 0 else 999999

    # պարզ progress (եթե մնացորդային խելոքություն ուզենաս՝ կավելացնենք)
    progress = min(total_invited + carry, need)

    release_db(conn)
    return {
        "level": level,
        "need": need,
        "progress": progress,
        "total_invited": total_invited
    }


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
    release_db(conn)
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
    release_db(conn)

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
    release_db(conn)


# =========================
# Minimal JSON API (webapp uses it)
# =========================
@app_web.route("/api/user/<int:user_id>")
def api_get_user(user_id):
    try:
        conn = db(); c = conn.cursor()
        c.execute("""
            SELECT username, balance, last_mine, language, vorn_balance
              FROM users
             WHERE user_id=%s
        """, (user_id,))
        row = c.fetchone()
        close_conn(conn, c, commit=False)

        if not row:
            return jsonify({"error": "User not found"}), 404

        username, balance, last_mine, language, vorn_balance = row
        return jsonify({
            "user_id": user_id,
            "username": username,
            "balance": balance,
            "last_mine": last_mine,
            "language": language or "en",
            "vorn_balance": float(vorn_balance) if vorn_balance is not None else 0.0
        })
    except Exception as e:
        try: close_conn(conn, c, commit=False)
        except: pass
        return jsonify({"ok": False, "error": "server_error", "detail": str(e)}), 500



@app_web.route("/api/_debug/balances/<int:user_id>")
def api_debug_balances(user_id):
    conn = db(); c = conn.cursor()
    c.execute("SELECT balance, COALESCE(vorn_balance,0) FROM users WHERE user_id=%s", (user_id,))
    row = c.fetchone(); release_db(conn)
    if not row:
        return jsonify({"ok": False, "error": "user not found"}), 404
    return jsonify({"ok": True, "balance": int(row[0] or 0), "vorn_balance": float(row[1] or 0)})


@app_web.route("/api/reflevel/state")
def api_reflevel_state():
    uid = int(request.args.get("uid", 0))
    if not uid:
        return jsonify({"ok": False, "error": "missing uid"}), 400
    st = get_ref_level_state(uid)
    return jsonify({"ok": True, **st})


@app_web.route("/api/reflevel/claim", methods=["POST"])
def api_reflevel_claim():
    data = request.get_json(force=True, silent=True) or {}
    uid = int(data.get("uid", 0))
    if not uid:
        return jsonify({"ok": False, "error": "missing uid"}), 400

    try:
        conn = db()
        c = conn.cursor()

        # բերում ենք օգտագործողի ընթացիկ լվլը և carry-ն
        c.execute("SELECT level, carried_invites FROM ref_progress WHERE user_id=%s", (uid,))
        row = c.fetchone()
        if not row:
            release_db(conn)
            return jsonify({"ok": False, "error": "state not initialized"}), 400

        level, carry = row
        idx = min(level, len(REF_LEVELS)) - 1
        if idx < 0:
            release_db(conn)
            return jsonify({"ok": False, "error": "invalid level"}), 400

        need = REF_LEVELS[idx]["need"]

        # հաշվում ենք քանի հոգի է հրավիրել
        c.execute("SELECT COUNT(*) FROM users WHERE inviter_id=%s", (uid,))
        total_invited = c.fetchone()[0] or 0

        if total_invited + carry < need:
            release_db(conn)
            return jsonify({"ok": False, "error": "not_enough_invites", "need": need, "have": total_invited+carry}), 400

        # Reward տվյալներ
        feathers = REF_LEVELS[idx]["feathers"]
        vorn = REF_LEVELS[idx]["vorn"]

        # վերցնում ենք օգտագործողի ընթացիկ բալանսները
        c.execute("SELECT balance, vorn_balance FROM users WHERE user_id=%s", (uid,))
        from decimal import Decimal

        ub = c.fetchone() or (0, Decimal("0.0"))
        vorn_val = Decimal(str(vorn))
        new_b = int(ub[0] or 0) + int(feathers)
        new_v = Decimal(ub[1] or 0) + vorn_val


        # թարմացնում ենք բազան
        c.execute("UPDATE users SET balance=%s, vorn_balance=%s WHERE user_id=%s", (new_b, new_v, uid))

        # advance level, reset carry
        new_level = level + 1
        c.execute(
            "UPDATE ref_progress SET level=%s, carried_invites=%s, updated_at=%s WHERE user_id=%s",
            (new_level, 0, int(time.time()), uid)
        )

        conn.commit()
        release_db(conn)

        # վերադարձնում ենք JSON պատասխանը
        return jsonify({
            "ok": True,
            "level_was": level,
            "level_now": new_level,
            "reward_feathers": feathers,
            "reward_vorn": vorn,
            "new_balance": new_b,
            "new_vorn": new_v
        })

    except Exception as e:
        try:
            release_db(conn)
        except Exception:
            pass
        return jsonify({"ok": False, "error": str(e)}), 500



@app_web.route("/api/set_language", methods=["POST"])
def api_set_language():
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    lang = (data.get("language") or "en").lower()[:8]
    allowed_langs = (
        "en","ru","hy","fr","es","de","it","tr","fa","ar","zh","ja","ko",
        "hi","pt","el","pl","nl","sv","ro","hu","cs","uk","az","ka"
    )
    if lang not in allowed_langs:
        lang = "en"

    if not user_id:
        return jsonify({"ok": False, "error": "missing user_id"}), 400

    conn = db(); c = conn.cursor()
    c.execute("UPDATE users SET language=%s WHERE user_id=%s", (lang, user_id))
    close_conn(conn, c, commit=True)
    return jsonify({"ok": True, "language": lang})



@app_web.route("/api/mine", methods=["POST"])
def api_mine():
    try:
        data = request.get_json(force=True, silent=True) or {}
        user_id = int(data.get("user_id", 0))
        if not user_id:
            return jsonify({"ok": False, "error": "missing user_id"}), 400

        # ստուգում ենք cooldown-ը
        ok, remaining = can_mine(user_id)
        if not ok:
            return jsonify({"ok": False, "error": "cooldown_active", "remaining": remaining}), 200

        # գումարում ենք փետուրները
        new_bal = update_balance(user_id, MINE_REWARD)
        set_last_mine(user_id)
        now_ts = int(time.time())

        # վերցնում ենք լեզուն
        conn = db(); c = conn.cursor()
        c.execute("SELECT language FROM users WHERE user_id=%s", (user_id,))
        row = c.fetchone()
        release_db(conn)
        lang = row[0] if row and row[0] else "en"

        print(f"✅ Mined {MINE_REWARD} by user {user_id}")
        return jsonify({
            "ok": True,
            "reward": MINE_REWARD,
            "balance": new_bal,
            "last_mine": now_ts,
            "language": lang
        }), 200

    except Exception as e:
        print("🔥 Error in /api/mine:", e)
        return jsonify({"ok": False, "error": "server_error"}), 500






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
            c.execute("""
            UPDATE users
           SET vorn_balance = COALESCE(vorn_balance, 0)::NUMERIC(20,6) + %s::NUMERIC(20,6)
         WHERE user_id = %s
         RETURNING vorn_balance
        """, (amount, user_id))
        vbal = c.fetchone()[0]



                
        close_conn(conn, c, commit=True)
        print(f"🜂 Added {amount} VORN to {user_id}, new total = {vbal}")
        add_referral_bonus(user_id, reward_feathers=0, reward_vorn=amount)
        return jsonify({"ok": True, "vorn_added": amount, "vorn_balance": vbal})


    except Exception as e:
        print("🔥 /api/vorn_reward failed:", e)
        return jsonify({"ok": False, "error": str(e)}), 500



# ==========================================
# 🔗 REFERRALS SYSTEM API
# ==========================================

from flask import request, jsonify
import math



# 🪶 Level progression (հիմնված քո նշած արժեքների վրա)
REF_LEVELS = [
    {"lvl": 1, "need": 3, "feathers": 3000, "vorn": 0.5},
    {"lvl": 2, "need": 5, "feathers": 5000, "vorn": 0.7},
    {"lvl": 3, "need": 8, "feathers": 8000, "vorn": 1.0},
    {"lvl": 4, "need": 10, "feathers": 10000, "vorn": 1.2},
    {"lvl": 5, "need": 12, "feathers": 12000, "vorn": 1.4},
    {"lvl": 6, "need": 14, "feathers": 14000, "vorn": 1.6},
    {"lvl": 7, "need": 16, "feathers": 16000, "vorn": 1.8},
    {"lvl": 8, "need": 18, "feathers": 18000, "vorn": 2.0},
    {"lvl": 9, "need": 20, "feathers": 20000, "vorn": 2.2},
    {"lvl": 10, "need": 22, "feathers": 22000, "vorn": 2.4},
    {"lvl": 11, "need": 42, "feathers": 42000, "vorn": 4.5},
    {"lvl": 12, "need": 100, "feathers": 100000, "vorn": 10.0},
    {"lvl": 13, "need": 160, "feathers": 160000, "vorn": 18.0},
    {"lvl": 14, "need": 220, "feathers": 220000, "vorn": 27.0},
    {"lvl": 15, "need": 300, "feathers": 300000, "vorn": 40.0},
]


def get_ref_level_data(uid):
    invited = len(user_referrals.get(uid, []))
    cur_lvl = user_levels.get(uid, 1)
    next_lvl = REF_LEVELS[min(cur_lvl, len(REF_LEVELS)) - 1]
    return invited, cur_lvl, next_lvl




@app_web.route("/api/vorn_exchange", methods=["POST"])
def api_vorn_exchange():
    """
    Converts Feathers (🪶) into VORN (🜂)
    50_000 Feathers = 1 🜂
    Atomic SQL + proper connection closing.
    """
    data = request.get_json(force=True, silent=True) or {}
    uid = int(data.get("user_id", 0))
    if not uid:
        return jsonify({"ok": False, "error": "missing user_id"}), 400

    COST = 50000
    REWARD = 1.0 
    
    try:
        conn = db()
        cur = conn.cursor()

        # ensure vorn_balance exists (safe)
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS vorn_balance NUMERIC(20,6) DEFAULT 0")
        except Exception:
            pass

        # ATOMIC: one UPDATE that both subtracts feathers and adds vorn
        cur.execute("""
            UPDATE users
                SET balance      = balance - %s,
                vorn_balance = COALESCE(vorn_balance, 0)::NUMERIC(20,6) + %s::NUMERIC(20,6)
             WHERE user_id = %s AND balance >= %s
             RETURNING balance, vorn_balance
        """, (COST, REWARD, uid, COST))


        row = cur.fetchone()
        if not row:
            close_conn(conn, cur, commit=False)
            return jsonify({"ok": False, "error": "not_enough_feathers"}), 200

        new_balance, new_vorn = row
        close_conn(conn, cur, commit=True)

        # 3% referral accrual ONLY after successful exchange (non-blocking)
        try:
            add_referral_bonus(uid, reward_feathers=0, reward_vorn=1.0)
        except Exception:
            pass

        return jsonify({
            "ok": True,
            "spent_feathers": COST,
            "new_balance": int(new_balance),
            "new_vorn": float(new_vorn)
        }), 200

    except Exception as e:
        try:
            close_conn(conn, cur, commit=False)
        except Exception:
            pass
        return jsonify({"ok": False, "error": "server_error", "detail": str(e)}), 500



@app_web.route("/api/referral_claim", methods=["POST"])
def api_referral_claim():
    """Հաշվում և տալիս է հրավիրողի 3% բոնուսը բոլոր նոր եկամուտներից"""
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    if not user_id:
        return jsonify({"ok": False, "error": "missing user_id"}), 400

    conn = db(); c = conn.cursor()
    c.execute("SELECT SUM(amount_feathers), SUM(amount_vorn) FROM referral_earnings WHERE inviter_id=%s", (user_id,))
    row = c.fetchone()
    total_f = int(row[0] or 0)
    total_v = float(row[1] or 0)

    # զրոյացնում ենք ցուցակը
    c.execute("""
    UPDATE referral_earnings
    SET amount_feathers = 0, amount_vorn = 0
    WHERE inviter_id = %s
""", (user_id,))

    # Թարմացնում ենք հաշվեկշիռը
    c.execute("SELECT balance, vorn_balance FROM users WHERE user_id=%s", (user_id,))
    r2 = c.fetchone()
    if r2:
        new_b = r2[0] + total_f
        new_v = r2[1] + total_v
        c.execute("UPDATE users SET balance=%s, vorn_balance=%s WHERE user_id=%s", (new_b, new_v, user_id))
    conn.commit(); release_db(conn)
    return jsonify({"ok": True, "claimed_feathers": total_f, "claimed_vorn": total_v})


@app_web.route("/api/tasks")
def api_tasks():
    import time
    uid = int(request.args.get("uid", 0))
    conn = db(); c = conn.cursor()

    c.execute("""
        SELECT id, type, title, reward_feather, reward_vorn, link
          FROM tasks
         WHERE active=TRUE
         ORDER BY id DESC
    """)
    rows = c.fetchall()

    today = time.strftime("%Y-%m-%d")
    done_main, done_daily = set(), set()
    if uid:
        c.execute("SELECT task_id FROM user_tasks WHERE user_id=%s AND date_key='ALL_TIME'", (uid,))
        done_main = {r[0] for r in c.fetchall()}
        c.execute("SELECT task_id FROM user_tasks WHERE user_id=%s AND date_key=%s", (uid, today))
        done_daily = {r[0] for r in c.fetchall()}

    data = {"main": [], "daily": []}
    for tid, ttype, title, rf, rv, link in rows:
        completed = tid in (done_daily if ttype == "daily" else done_main)
        data[ttype].append({
            "id": tid,
            "title": title,
            "reward_feather": rf or 0,
            "reward_vorn": rv or 0.0,
            "link": link or "",
            "completed": completed
        })

    release_db(conn)
    return jsonify(data)


# ---------- USER STATS COMMAND ----------
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users;")
    total = c.fetchone()[0]
    await update.message.reply_text(f"Total users: {total}")


@app_web.route("/api/ref_link/<int:user_id>")
def api_ref_link(user_id: int):
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
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
    conn.commit(); release_db(conn)

def list_tasks(task_type: str):
    conn = db(); c = conn.cursor()
    c.execute("""
        SELECT id, title, reward, link, description
        FROM tasks
        WHERE type=%s AND active=1
        ORDER BY id DESC
    """, (task_type,))
    rows = c.fetchall(); release_db(conn)
    return rows

async def btn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles inline button clicks — temporarily just acknowledges them."""
    query = update.callback_query
    await query.answer("OK")


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
        VALUES (%s, %s, %s, %s, %s, %s, TRUE)
    """, (task_type, title, int(reward_feather), float(reward_vorn), link, int(time.time())))


    conn.commit(); release_db(conn)


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
    conn.commit(); release_db(conn)
    await update.message.reply_text(f"🗑️ Task {tid} deleted.")


async def listtasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("⛔ Not authorized.")
    conn = db(); c = conn.cursor()
    c.execute("SELECT id, type, title, reward_feather, reward_vorn FROM tasks WHERE active = TRUE ORDER BY id DESC")
    rows = c.fetchall(); release_db(conn)
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
    conn.commit(); release_db(conn)

    return jsonify({"ok": True, "token": token})


# =========================
# Static legal pages (Terms + Privacy)
# =========================
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app_web.route('/terms.html')
def serve_terms():
    return send_from_directory(os.path.join(BASE_DIR, 'webapp'), 'terms.html')


@app_web.route('/privacy.html')
def serve_privacy():
    return send_from_directory(os.path.join(BASE_DIR, 'webapp'), 'privacy.html')


# --- TikTok site verification: serve token file from root ---
@app_web.route("/tiktokxIdyn8EdBKD9JpuXubuRGoh4vXfVZF18.txt")
def serve_tiktok_verif_standard():
    return send_from_directory(BASE_DIR, "tiktokxIdyn8EdBKD9JpuXubuRGoh4vXfVZF18.txt")

# --- TikTok URL prefix verification (serve as plain text at site root) ---
@app_web.route("/tiktok-developers-site-verification.txt")
def tiktok_verification_file():
    return "tiktok-developers-site-verification=xIdyn8EdBKD9JpuXubuRGoh4vXfVZF18", 200, {
        "Content-Type": "text/plain; charset=utf-8"
    }




@app_web.route("/api/task_attempt_verify", methods=["POST"])
def api_task_attempt_verify():
    import time
    user_id = int(request.json.get("user_id", 0))
    task_id = int(request.json.get("task_id", 0))
    token   = str(request.json.get("token", ""))

    if not user_id or not task_id or not token:
        return jsonify({"ok": False, "error": "missing_fields"}), 400

    conn = db(); c = conn.cursor()

    # --- ստուգում ենք token-ը ---
    c.execute("SELECT id, status FROM task_attempts WHERE user_id=%s AND task_id=%s AND token=%s",
              (user_id, task_id, token))
    row = c.fetchone()
    if not row:
        release_db(conn)
        return jsonify({"ok": False, "error": "invalid_token"}), 400
    if row[1] == "verified":
        release_db(conn)
        return jsonify({"ok": False, "error": "already_verified"}), 400

    # --- վերցնում ենք task-ի տեսակը ու պարգևները ---
    c.execute("SELECT type, reward_feather, reward_vorn FROM tasks WHERE id=%s AND active=TRUE", (task_id,))
    trow = c.fetchone()
    if not trow:
        release_db(conn)
        return jsonify({"ok": False, "error": "task_not_found"}), 404

    task_type, reward_feather, reward_vorn = trow

    # --- date_key = daily → այսօր, main → ALL_TIME ---
    date_key = time.strftime("%Y-%m-%d") if task_type == "daily" else "ALL_TIME"

    # --- եթե արդեն արված է՝ չհաշվենք նորից ---
    c.execute("SELECT 1 FROM user_tasks WHERE user_id=%s AND task_id=%s AND date_key=%s",
              (user_id, task_id, date_key))
    if c.fetchone():
        release_db(conn)
        return jsonify({"ok": False, "error": "already_completed"}), 400

    # --- նշում ենք verify արված ---
    c.execute("UPDATE task_attempts SET status='verified', verified_at=%s WHERE id=%s", (int(time.time()), row[0]))
    c.execute("INSERT INTO user_tasks (user_id, task_id, date_key, completed_at) VALUES (%s,%s,%s,%s)",
              (user_id, task_id, date_key, int(time.time())))

    # --- գումարում ենք պարգևը ---
    c.execute("SELECT balance, COALESCE(vorn_balance,0) FROM users WHERE user_id=%s", (user_id,))
    ub = c.fetchone() or (0, 0)
    new_balance = ub[0] + int(reward_feather or 0)
    new_vorn = float(ub[1]) + float(reward_vorn or 0)

    c.execute("""
        UPDATE users
           SET balance = %s,
               vorn_balance = %s
         WHERE user_id = %s
    """, (new_balance, new_vorn, user_id))
    conn.commit()
    release_db(conn)

    # --- optional referral bonus ---
    try:
        add_referral_bonus(user_id,
                           reward_feathers=int(reward_feather or 0),
                           reward_vorn=float(reward_vorn or 0.0))
    except Exception as e:
        print("ref bonus error:", e)

    return jsonify({
        "ok": True,
        "reward_feather": int(reward_feather or 0),
        "reward_vorn": float(reward_vorn or 0.0),
        "new_balance": new_balance,
        "new_vorn": new_vorn
    })



@app_web.route("/api/task_attempt_verify_forced", methods=["POST"])
def api_task_attempt_verify_forced():
    """
    iPhone FIX — force-complete task without external redirect.
    Called when user returns after clicking the task link.
    """

    import time
    data = request.get_json(force=True, silent=True) or {}
    user_id = int(data.get("user_id", 0))
    task_id = int(data.get("task_id", 0))

    if not user_id or not task_id:
        return jsonify({"ok": False, "error": "missing user_id or task_id"}), 400

    conn = db(); c = conn.cursor()

    # Load task info
    c.execute("SELECT type, reward_feather, reward_vorn FROM tasks WHERE id=%s AND active=TRUE", (task_id,))
    trow = c.fetchone()
    if not trow:
        release_db(conn)
        return jsonify({"ok": False, "error": "task_not_found"}), 404

    task_type, reward_feather, reward_vorn = trow
    date_key = time.strftime("%Y-%m-%d") if task_type == "daily" else "ALL_TIME"

    # Check if already completed
    c.execute("SELECT 1 FROM user_tasks WHERE user_id=%s AND task_id=%s AND date_key=%s",
              (user_id, task_id, date_key))
    if c.fetchone():
        release_db(conn)
        return jsonify({"ok": False, "error": "already_completed"}), 400

    # Mark completed
    c.execute("""
        INSERT INTO user_tasks (user_id, task_id, date_key, completed_at)
        VALUES (%s, %s, %s, %s)
    """, (user_id, task_id, date_key, int(time.time())))

    # Update balance
    c.execute("SELECT balance, COALESCE(vorn_balance, 0) FROM users WHERE user_id=%s", (user_id,))
    ub = c.fetchone() or (0, 0)

    new_balance = ub[0] + int(reward_feather or 0)
    new_vorn = float(ub[1]) + float(reward_vorn or 0)

    c.execute("""
        UPDATE users
        SET balance=%s, vorn_balance=%s
        WHERE user_id=%s
    """, (new_balance, new_vorn, user_id))

    conn.commit()
    release_db(conn)

    try:
        add_referral_bonus(
            user_id,
            reward_feathers=int(reward_feather or 0),
            reward_vorn=float(reward_vorn or 0.0)
        )
    except Exception as e:
        print("ref bonus error:", e)

    return jsonify({
        "ok": True,
        "forced": True,
        "reward_feather": int(reward_feather or 0),
        "reward_vorn": float(reward_vorn or 0),
        "new_balance": new_balance,
        "new_vorn": new_vorn
    })


# =========================
# VERIFY TASK — Reward distribution
# =========================

@app_web.route("/api/verify_task", methods=["POST"])
def api_verify_task():
    return jsonify({"ok": False, "error": "deprecated"}), 410
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
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS vorn_balance NUMERIC(20,6) DEFAULT 0")
    except Exception:
        pass

    # read task info
    c.execute("SELECT reward_feather, reward_vorn FROM tasks WHERE id=%s AND active = TRUE", (task_id,))
    task = c.fetchone()
    if not task:
        release_db(conn)
        return jsonify({"ok": False, "error": "task not found"}), 404

    reward_feather, reward_vorn = task

    # check if already done
    date_key = time.strftime("%Y-%m-%d")
    c.execute("""
    UPDATE users
       SET balance      = (COALESCE(balance,0) + %s),
           vorn_balance = COALESCE(vorn_balance,0)::NUMERIC(20,6) + %s::NUMERIC(20,6)
     WHERE user_id = %s
    """, (reward_feather, reward_vorn, user_id))

    if c.fetchone():
        release_db(conn)
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
    conn.commit(); release_db(conn)

    add_referral_bonus(user_id, reward_feather, reward_vorn)


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
    if not user:
        return

    # 🧩 inviter_id /start ref_xxx
    text = update.message.text if update.message else ""
    inviter_id = None
    if text and text.startswith("/start"):
        parts = text.split()
        if len(parts) > 1 and parts[1].startswith("ref_"):
            try:
                inviter_id = int(parts[1].replace("ref_", ""))
            except Exception:
                inviter_id = None

    # ❌ self-referral block
    if inviter_id == user.id:
        inviter_id = None

    # 🧩 ensure user in DB
    ensure_user(user.id, user.username, inviter_id)

    # 🌐 WebApp URL
    base = (PUBLIC_BASE_URL or "https://vorn-bot-nggr.onrender.com").rstrip("/")
    wa_url = f"{base}/app?uid={user.id}"

    # 🌍 լեզուն
    user_lang = get_user_language(user.id)
    button_text = INVITE_BUTTONS.get(user_lang, INVITE_BUTTONS["en"])

    # 🔘 keyboard — Open App + Share Button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🌀 OPEN APP", web_app=WebAppInfo(url=wa_url))],
        [InlineKeyboardButton(text=button_text, switch_inline_query=f"vorn_{user.id}")]
    ])

    # ✉️ ուղարկում ենք մեսիջը նորմալ async-ով
    msg = await context.bot.send_message(
        chat_id=user.id,
        text="🌕 Press the button to enter VORN App 👇",
        reply_markup=keyboard
    )

    # 📌 փորձում ենք pin անել /start մեսիջը
    try:
        if update.message:
            await context.bot.pin_chat_message(
                chat_id=user.id,
                message_id=update.message.message_id
            )
    except Exception:
        pass


    user_lang = get_user_language(user.id)
    button_text = INVITE_BUTTONS.get(user_lang, INVITE_BUTTONS["en"])

    share_keyboard = InlineKeyboardMarkup([
    [InlineKeyboardButton(text=button_text, switch_inline_query=f"vorn_{user.id}")]
])


async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.inline_query.query

    if q.startswith("vorn_"):
        uid = int(q.replace("vorn_", ""))

        user_lang = get_user_language(uid)
        txt = INVITE_TEXTS.get(user_lang, INVITE_TEXTS["en"])

        ref = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
        final_text = txt.format(ref=ref)

        results = [
            InlineQueryResultArticle(
                id="1",
                title="VORN Invite",
                description="Send invitation message",
                thumb_url="https://yourcdn.com/vorn_share.png",
                input_message_content=InputTextMessageContent(final_text)
            )
        ]

        await update.inline_query.answer(results, cache_time=0)


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
    application.add_handler(CallbackQueryHandler(btn_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, block_text))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(InlineQueryHandler(inline_query_handler))


    # ✅ Proper initialization (NEW FIX)
    await application.initialize()

    # Webhook URL
    port = int(os.environ.get("PORT", "10000"))
    webhook_url = f"{PUBLIC_BASE_URL}/webhook"

    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(url=webhook_url)
    print(f"✅ Webhook set to {webhook_url}")

    try:
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🌀 VORN App", web_app=WebAppInfo(url=f"{PUBLIC_BASE_URL}/app")
            )
        )
        print("✅ Global menu button → WebApp")
    except Exception as e:
        print("⚠️ Failed to set menu button:", e)

    # ✅ Սա ավելացրու այն տեղում, որտեղ նախկինում «Proper start» էր գրված

# ✅ Proper start (FINAL FIX)
async def run_telegram_bot():
    try:
        await application.start()
        print("✅ Telegram bot started and listening for updates (Webhook mode).")
    except Exception as e:
        print("🔥 Failed to start Telegram bot:", e)

# 🚀 Launch bot in background (safe task)
    asyncio.create_task(run_telegram_bot())

# Keep running forever
    await asyncio.Event().wait()



from flask import request, jsonify
import asyncio
import threading

@app_web.route("/webhook", methods=["POST"])
def telegram_webhook():
    global application

    if application is None:
        print("❌ application is None — bot not ready")
        return jsonify({"ok": False, "error": "bot not ready"}), 503

    update_data = request.get_json(force=True, silent=True)
    if not update_data:
        print("⚠️ Empty update received")
        return jsonify({"ok": False, "error": "empty update"}), 400

    try:
        upd = Update.de_json(update_data, application.bot)
        print("📩 Telegram update received")

        def process_update_safely():
            try:
                loop = application._loop
                asyncio.run_coroutine_threadsafe(
                    application.process_update(upd),
                    loop
                )
            except Exception as e:
                print("🔥 process_update_safely error:", e)

        threading.Thread(
            target=process_update_safely,
            daemon=True
        ).start()

        return jsonify({"ok": True}), 200

    except Exception as e:
        print("🔥 Webhook error:", e)
        return jsonify({"ok": False, "error": str(e)}), 500


# === SUPPORT BOT WEBHOOK (Render-safe) ===
from support_bot import start_support_runtime, enqueue_support_update

# 🟢 Գործարկում ենք Support bot-ը Render-ի միջավայրում (առանձին event loop-ում)
start_support_runtime()

@app_web.route("/support", methods=["POST"])
def support_webhook():
    from flask import request, jsonify
    try:
        data = request.get_json(silent=True, force=True) or {}
        print("📩 Support webhook received:", data)
        enqueue_support_update(data)
        print("✅ Support update enqueued successfully.")
        return jsonify({"ok": True}), 200
    except Exception as e:
        import traceback
        print("🔥 Support webhook error:", e)
        print(traceback.format_exc())
        return jsonify({"ok": False, "error": str(e)}), 500








# =====================================================
# 🌐 GOOGLE AUTH (for YouTube verification & analytics)
# =====================================================
from flask import redirect, session
import requests

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = f"{PUBLIC_BASE_URL}/auth/google/callback"
GOOGLE_AUTH_SCOPE = "https://www.googleapis.com/auth/youtube.readonly https://www.googleapis.com/auth/userinfo.profile"

@app_web.route("/auth/google")
def google_auth():
    """Redirect user to Google OAuth page"""
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
    """Handle OAuth response and exchange code for tokens"""
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

    # save or inspect token
    access_token = tokens.get("access_token")
    if not access_token:
        return f"❌ Token exchange failed: {tokens}", 400

    # Example: fetch YouTube info
    headers = {"Authorization": f"Bearer {access_token}"}
    yt_resp = requests.get("https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true", headers=headers)
    data = yt_resp.json()

    return jsonify({"ok": True, "youtube": data})


# =====================================================
# 🧩 Referral unified API (for WebApp frontend)
# =====================================================

@app_web.route("/api/referrals")
def api_referrals_list():
    """Return invited friends + their stats + count for given uid"""
    uid = int(request.args.get("uid", 0))
    if not uid:
        return jsonify({"ok": False, "error": "missing uid"}), 400

    try:
        conn = db(); c = conn.cursor()
        # բոլոր հրավիրվածների ցուցակը
        c.execute("""
            SELECT user_id, username, balance, vorn_balance
            FROM users
            WHERE inviter_id = %s
            ORDER BY balance DESC
        """, (uid,))
        rows = c.fetchall()

        invited_count = len(rows)

        data = []
        for i, (rid, uname, feathers, vorn) in enumerate(rows, start=1):
            data.append({
                "rank": i,
                "username": uname or f"User{rid}",
                "feathers": feathers or 0,
                "vorn": float(vorn or 0)
            })

        close_conn(conn, c, commit=False)

        return jsonify({
            "ok": True,
            "invited_count": invited_count,
            "list": data,
            "levels": REF_LEVELS   # 👈 Ավելացրու այս տողը
        })

    except Exception as e:
        try:
            close_conn(conn, c, commit=False)
        except Exception:
            pass
        return jsonify({"ok": False, "error": "server_error", "detail": str(e)}), 500



@app_web.route("/api/referrals/preview")
def api_referrals_preview():
    uid = int(request.args.get("uid", 0))
    if not uid:
        return jsonify({"ok": False, "error": "missing uid"}), 400
    try:
        conn = db(); c = conn.cursor()
        c.execute("""
            SELECT SUM(amount_feathers), SUM(amount_vorn)
              FROM referral_earnings
             WHERE inviter_id=%s
        """, (uid,))
        row = c.fetchone()
        close_conn(conn, c, commit=False)

        total_f = int(row[0] or 0)
        total_v = float(row[1] or 0)

        return jsonify({"ok": True, "cashback_feathers": total_f, "cashback_vorn": total_v})
    except Exception as e:
        try: close_conn(conn, c, commit=False)
        except: pass
        return jsonify({"ok": False, "error": "server_error", "detail": str(e)}), 500




@app_web.route("/api/referrals/claim", methods=["POST"])
def api_referrals_claim():
    data = request.get_json(force=True, silent=True) or {}
    uid = int(data.get("uid", 0))
    if not uid:
        return jsonify({"ok": False, "error": "missing uid"}), 400
    try:
        conn = db(); c = conn.cursor()
        c.execute("""
            SELECT SUM(amount_feathers), SUM(amount_vorn)
              FROM referral_earnings
             WHERE inviter_id=%s
        """, (uid,))
        row = c.fetchone()
        total_f = int(row[0] or 0)
        total_v = float(row[1] or 0)

        c.execute("DELETE FROM referral_earnings WHERE inviter_id=%s", (uid,))

        c.execute("SELECT balance, vorn_balance FROM users WHERE user_id=%s", (uid,))
        row2 = c.fetchone()
        from decimal import Decimal

        if row2:
            old_balance = int(row2[0] or 0)
            old_vorn = Decimal(str(row2[1] or 0))
            total_v_dec = Decimal(str(total_v))

            new_b = old_balance + int(total_f or 0)
            new_v = old_vorn + total_v_dec

            c.execute("""
                UPDATE users
                SET balance = %s,
                vorn_balance = %s
                WHERE user_id = %s
            """, (new_b, new_v, uid))



        close_conn(conn, c, commit=True)
        return jsonify({
            "ok": True,
            "cashback_feathers": total_f,
            "cashback_vorn": total_v,
            "new_balance": new_b,
            "new_vorn": new_v
        })
    except Exception as e:
        try: close_conn(conn, c, commit=False)
        except: pass
        return jsonify({"ok": False, "error": "server_error", "detail": str(e)}), 500



@app_web.route("/api/reflevel/check", methods=["POST"])
def api_reflevel_check():
    """
    Called from frontend to re-check if user reached a new level
    and give the corresponding bonus automatically.
    """
    data = request.get_json(force=True, silent=True) or {}
    uid = int(data.get("uid", 0))
    if not uid:
        return jsonify({"ok": False, "error": "missing uid"}), 400

    try:
        check_ref_level_progress(uid)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ==========================================
# 🕐 KEEP-ALIVE (Render-safe background ping)
# ==========================================
import threading, requests, time

def keep_alive():
    url = "https://vorn-bot-nggr.onrender.com"  # ⚠️ փոխիր քո իրական Render domain-ով
    while True:
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                print("🟢 Keep-alive ping successful.")
            else:
                print(f"⚠️ Keep-alive status: {res.status_code}")
        except Exception as e:
            print("⚠️ Keep-alive failed:", e)
        time.sleep(600)  # ամեն 10 րոպեն մեկ (600 վրկ)

# Ֆոնային թելը՝ սկսվում է անմիջապես
threading.Thread(target=keep_alive, daemon=True).start()

@app_web.route("/debug/referrals")
def debug_referrals():
    conn = db(); c = conn.cursor()
    c.execute("SELECT inviter_id, referred_id, amount_feathers, amount_vorn FROM referral_earnings ORDER BY id DESC LIMIT 20;")
    rows = c.fetchall(); release_db(conn)
    return jsonify(rows)


@app_web.route("/test_register_ref", methods=["POST"])
def test_register_ref():
    """
    Փոքրիկ օգնողական route՝ ֆեյք օգտատեր գրանցելու համար՝ referral համակարգի ստուգման նպատակով։
    Օրինակ՝
    curl -X POST https://vorn-bot-nggr.onrender.com/test_register_ref \
      -H "Content-Type: application/json" \
      -d "{\"uid\":222222, \"inviter\":5274439601}"
    """
    data = request.get_json(force=True, silent=True) or {}
    uid = int(data.get("uid", 0))
    inviter = int(data.get("inviter", 0))
    if not uid or not inviter:
        return jsonify({"ok": False, "error": "missing uid or inviter"}), 400

    ensure_user(uid, f"test_user_{uid}", inviter)
    return jsonify({"ok": True, "uid": uid, "inviter": inviter})


@app_web.route("/test_add_feathers", methods=["POST"])
def test_add_feathers():
    data = request.get_json(force=True, silent=True) or {}
    uid = int(data.get("uid", 0))
    amount = int(data.get("amount", 0))
    if not uid or not amount:
        return jsonify({"ok": False, "error": "missing uid or amount"}), 400

    new_bal = update_balance(uid, amount)
    add_referral_bonus(uid, reward_feathers=amount, reward_vorn=0.0)
    return jsonify({"ok": True, "added": amount, "new_balance": new_bal})


@app_web.route("/api/fix_vorn_column")
def api_fix_vorn_column():
    """Migrate vorn_balance to NUMERIC(20,6) and fix NULLs."""
    try:
        conn = db(); c = conn.cursor()

        # 1) ensure column exists
        c.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS vorn_balance NUMERIC(20,6) DEFAULT 0")

        # 2) fix NULL/blank values to 0
        c.execute("""
            UPDATE users
               SET vorn_balance = 0
             WHERE vorn_balance IS NULL
                OR trim(vorn_balance::text) = ''
        """)

        # 3) convert any wrong types to NUMERIC(20,6)
        c.execute("""
            ALTER TABLE users
            ALTER COLUMN vorn_balance TYPE NUMERIC(20,6)
            USING COALESCE(vorn_balance, 0)::NUMERIC(20,6)
        """)

        # 4) keep not null + default
        c.execute("""
            ALTER TABLE users
            ALTER COLUMN vorn_balance SET DEFAULT 0,
            ALTER COLUMN vorn_balance SET NOT NULL
        """)

        conn.commit(); release_db(conn)
        return jsonify({"ok": True, "migrated": True})
    except Exception as e:
        try: release_db(conn)
        except: pass
        return jsonify({"ok": False, "error": str(e)}), 500



async def run_bot():
    """Runs Telegram bot in webhook mode and keeps the loop alive."""
    try:
        # 1) Initialize + set webhook
        await start_bot_webhook()

        # 2) Start Application (creates tasks, assigns .loop)
        await application.start()
        print("✅ Telegram bot started and listening for updates (Webhook mode).")

        # 3) Keep the bot alive forever
        await asyncio.Event().wait()

    except Exception as e:
        print("🔥 run_bot error:", e)



if __name__ == "__main__":
    print("✅ Bot script loaded successfully.")

    try:
        init_db()
        print("✅ Database initialized (PostgreSQL ready).")
    except Exception as e:
        print("⚠️ init_db() failed:", e)

    # --- Run Telegram bot in background thread ---
    def start_bot_thread():
        try:
            asyncio.run(run_bot())
        except Exception as e:
            print("🔥 Telegram bot thread crashed:", e)

    bot_thread = threading.Thread(target=start_bot_thread, daemon=True)
    bot_thread.start()

    # --- Run Flask as MAIN PROCESS for Render ---
    port = int(os.environ.get("PORT", "10000"))
    print(f"🌍 Flask starting on port {port} ...")

    app_web.run(
        host="0.0.0.0",
        port=port,
        threaded=True,
        use_reloader=False
    )








