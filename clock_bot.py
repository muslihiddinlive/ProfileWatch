"""
Jonli Soat Boti — clock_bot.py
ENV o'zgaruvchilar:
  API_ID, API_HASH, SESSION_STR, OWNER_ID
  BIO_TEXT (ixtiyoriy) — profil bio matni
  PORT (ixtiyoriy, default 8080)
"""

import sys

if "--get-session" in sys.argv:
    from pyrogram import Client
    print("=" * 50)
    print("  SESSION_STR generatsiya qilish")
    print("=" * 50)
    api_id   = int(input("API_ID   : "))
    api_hash = input("API_HASH : ").strip()
    with Client("_tmp_session", api_id=api_id, api_hash=api_hash) as tmp:
        session_str = tmp.export_session_string()
    print("\n✅ SESSION_STR:\n")
    print(session_str)
    print()
    sys.exit(0)

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

API_ID      = int(os.environ["API_ID"])
API_HASH    = os.environ["API_HASH"]
SESSION_STR = os.environ["SESSION_STR"]
OWNER_ID    = int(os.environ["OWNER_ID"])
PORT        = int(os.environ.get("PORT", 8080))
BIO_TEXT    = os.environ.get("BIO_TEXT", "").strip()

TIMEZONE = ZoneInfo("Asia/Tashkent")

# ─── DEFAULT SHRIFT (❶❽:❺⓿ uslubi) ─────────────────────────────────────────
DEFAULT_MAP = {
    "0": "⓿", "1": "❶", "2": "❷", "3": "❸", "4": "❹",
    "5": "❺", "6": "❻", "7": "❼", "8": "❽", "9": "❾",
    ":": ":",
}

state = {
    "char_map":  {},
    "last_name": "",
    "clock_on":  True,
}

app = Client(
    name="clock_session",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STR,
)

flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "Jonli soat boti ishlayapti ✅", 200

@flask_app.route("/ping")
def ping():
    return "pong", 200

def translate_time(time_str: str, char_map: dict) -> str:
    return "".join(char_map.get(ch, ch) for ch in time_str)

def current_uzb_time() -> str:
    return datetime.now(TIMEZONE).strftime("%H:%M")

async def update_profile_name():
    # Bio ni bir marta o'rnatish
    if BIO_TEXT:
        try:
            await app.update_profile(bio=BIO_TEXT)
            logger.info(f"Bio o'rnatildi: {BIO_TEXT}")
        except Exception as e:
            logger.error(f"Bio o'rnatishda xato: {e}")

    while True:
        try:
            if state["clock_on"]:
                time_raw = current_uzb_time()
                active_map = state["char_map"] if state["char_map"] else DEFAULT_MAP
                time_str = translate_time(time_raw, active_map)
                new_name = f"⏰ {time_str}"

                if new_name != state["last_name"]:
                    await app.update_profile(first_name=new_name)
                    state["last_name"] = new_name
                    logger.info(f"Ism yangilandi: {new_name}")
        except Exception as e:
            logger.error(f"Ism yangilashda xato: {e}")

        await asyncio.sleep(60)

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
