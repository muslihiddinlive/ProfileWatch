"""
Jonli Soat Boti — clock_bot.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ishlatish:
  1) SESSION_STR olish uchun (bir martalik, local):
       python clock_bot.py --get-session

  2) Botni ishga tushurish (Render va boshqa serverlar):
       python clock_bot.py

ENV o'zgaruvchilar (Render → Environment):
  API_ID, API_HASH, SESSION_STR
  PORT (ixtiyoriy, default 8080)

Boshqarish: Telegramda "Saved Messages" (o'zingizga xabar) ga komanda yozing.
"""

import sys

# ─── SESSION GENERATSIYA REJIMI ──────────────────────────────────────────────
if "--get-session" in sys.argv:
    from pyrogram import Client

    print("=" * 50)
    print("  SESSION_STR generatsiya qilish")
    print("  (Bu faqat bir marta ishlatiladi)")
    print("=" * 50)
    api_id   = int(input("API_ID   : "))
    api_hash = input("API_HASH : ").strip()

    with Client("_tmp_session", api_id=api_id, api_hash=api_hash) as tmp:
        session_str = tmp.export_session_string()

    print("\n✅ SESSION_STR mana — Render ENV ga kiriting:\n")
    print(session_str)
    print()
    sys.exit(0)


# ─── ASOSIY BOT ──────────────────────────────────────────────────────────────

import os
import asyncio
import logging
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask
from pyrogram import Client, filters, idle
from pyrogram.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── ENV VARIABLES ───────────────────────────────────────────────────────────
API_ID      = int(os.environ["API_ID"])
API_HASH    = os.environ["API_HASH"]
SESSION_STR = os.environ["SESSION_STR"]
PORT        = int(os.environ.get("PORT", 8080))

TIMEZONE = ZoneInfo("Asia/Tashkent")

# ─── BOT HOLATI ──────────────────────────────────────────────────────────────
state = {
    "char_map":  {},
    "bio_extra": "",
    "waiting":   None,
    "last_name": "",
    "clock_on":  True,
}

DEFAULT_MAP = {
    "0":"0","1":"1","2":"2","3":"3","4":"4",
    "5":"5","6":"6","7":"7","8":"8","9":"9",
    ":":":",
}

# ─── PYROGRAM KLIENT ─────────────────────────────────────────────────────────
app = Client(
    name="clock_session",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STR,
)

# ─── FLASK (Render health-check) ─────────────────────────────────────────────
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "Jonli soat boti ishlayapti ✅", 200

@flask_app.route("/ping")
def ping():
    return "pong", 200

# ─── YORDAMCHI FUNKSIYALAR ───────────────────────────────────────────────────

def translate_time(time_str: str, char_map: dict) -> str:
    return "".join(char_map.get(ch, ch) for ch in time_str)

def current_uzb_time() -> str:
    return datetime.now(TIMEZONE).strftime("%H:%M")

async def update_profile_name():
    """Har daqiqada profil ismini yangilaydi."""
    while True:
        try:
            if state["clock_on"]:
                time_raw = current_uzb_time()
                active_map = state["char_map"] if state["char_map"] else DEFAULT_MAP
                time_str = translate_time(time_raw, active_map)
                new_name = f"🕐 {time_str}"

                if new_name != state["last_name"]:
                    await app.update_profile(first_name=new_name)
                    state["last_name"] = new_name
                    logger.info(f"Ism yangilandi: {new_name}")
        except Exception as e:
            logger.error(f"Ism yangilashda xato: {e}")

        await asyncio.sleep(60)

# ─── KOMANDALAR ──────────────────────────────────────────────────────────────

@app.on_message(filters.command("start") & filters.me)
async def cmd_start(client, message: Message):
    await message.reply(
        "👋 Salom! Jonli soat boti.\n\n"
        "📋 Komandalar:\n"
        "/style — Shrift belgilarini sozlash\n"
        "/bio — Bio ga qo'shimcha matn qo'shish\n"
        "/status — Joriy holat\n"
        "/stop — Soatni to'xtatish\n"
        "/resume — Soatni davom ettirish"
    )

@app.on_message(filters.command("style") & filters.me)
async def cmd_style(client, message: Message):
    state["waiting"] = "style"
    await message.reply(
        "🔤 Har bir raqam va belgi uchun xarita yuboring.\n\n"
        "Namuna:\n"
        "0=𝟎\n1=𝟏\n2=𝟐\n3=𝟑\n4=𝟒\n5=𝟓\n6=𝟔\n7=𝟕\n8=𝟖\n9=𝟗\n:=⁚\n\n"
        "Siz istagan emoji yoki belgi ishlatishingiz mumkin!\n"
        "Bekor qilish: /cancel"
    )

@app.on_message(filters.command("bio") & filters.me)
async def cmd_bio(client, message: Message):
    current = state["bio_extra"] or "(bo'sh)"
    state["waiting"] = "bio"
    await message.reply(
        f"📝 Hozirgi bio: {current}\n\n"
        "Yangi matn yuboring.\n"
        "Bo'sh qoldirish uchun: -\n"
        "Bekor qilish: /cancel"
    )

@app.on_message(filters.command("status") & filters.me)
async def cmd_status(client, message: Message):
    time_raw = current_uzb_time()
    active_map = state["char_map"] if state["char_map"] else DEFAULT_MAP
    time_str = translate_time(time_raw, active_map)
    map_display = "\n".join([f"  {k} → {v}" for k, v in active_map.items()])
    await message.reply(
        f"🕐 Joriy UZB vaqti: {time_raw}\n"
        f"🔤 Shrift bilan: {time_str}\n"
        f"📝 Bio: {state['bio_extra'] or '(yo\\'q)'}\n"
        f"⚙️ Soat: {'Yoqiq ✅' if state['clock_on'] else 'O\\'chiq ❌'}\n\n"
        f"Harf xaritasi:\n{map_display}"
    )

@app.on_message(filters.command("stop") & filters.me)
async def cmd_stop(client, message: Message):
    state["clock_on"] = False
    await message.reply("⏸ Soat to'xtatildi.")

@app.on_message(filters.command("resume") & filters.me)
async def cmd_resume(client, message: Message):
    state["clock_on"] = True
    await message.reply("▶️ Soat qayta boshlandi.")

@app.on_message(filters.command("cancel") & filters.me)
async def cmd_cancel(client, message: Message):
    state["waiting"] = None
    await message.reply("❌ Bekor qilindi.")

# ─── MATN XABARLARI ──────────────────────────────────────────────────────────

@app.on_message(filters.me & filters.text & ~filters.command(
    ["start","style","bio","status","stop","resume","cancel"]
))
async def handle_text(client, message: Message):

    if state["waiting"] == "style":
        lines = message.text.strip().split("\n")
        new_map = {}
        errors = []
        for line in lines:
            line = line.strip()
            if "=" not in line:
                errors.append(f"⚠️ Format xato: `{line}` (= belgisi yo'q)")
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip()
            if not key or not val:
                errors.append(f"⚠️ Bo'sh qiymat: `{line}`")
                continue
            new_map[key] = val

        if new_map:
            if ":" not in new_map:
                new_map[":"] = ":"
            state["char_map"] = new_map
            state["waiting"] = None
            state["last_name"] = ""
            example = translate_time("12:34", new_map)
            err_msg = "\n".join(errors) if errors else ""
            await message.reply(
                f"✅ Shrift saqlandi!\nNamuna (12:34): {example}\n{err_msg}"
            )
        else:
            await message.reply("❌ Hech qanday to'g'ri qiymat topilmadi.")
        return

    if state["waiting"] == "bio":
        bio_text = message.text.strip()
        if bio_text == "-":
            bio_text = ""

        if len(bio_text) > 70:
            await message.reply(
                f"❌ Bio uzun! {len(bio_text)} belgi, maksimal 70.\nQisqartiring."
            )
            return

        state["bio_extra"] = bio_text
        state["waiting"] = None
        try:
            await app.update_profile(bio=bio_text)
            await message.reply(f"✅ Bio yangilandi: {bio_text or '(bo\\'sh)'}")
        except Exception as e:
            await message.reply(f"⚠️ Telegramga yuborganda xato: {e}")
        return

    await message.reply("ℹ️ Biror komanda ishlating: /start")


# ─── ASOSIY ISHGA TUSHURISH ──────────────────────────────────────────────────

def run_flask():
    flask_app.run(host="0.0.0.0", port=PORT)

async def main():
    await app.start()
    logger.info("Pyrogram sessiyasi boshlandi.")
    asyncio.get_event_loop().create_task(update_profile_name())
    logger.info("Jonli soat vazifasi boshlandi.")
    await idle()
    await app.stop()

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info(f"Flask {PORT} portda ishga tushdi.")
    asyncio.run(main())
