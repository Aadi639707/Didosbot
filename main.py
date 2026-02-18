import os
import asyncio
import random
import string
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputStream
from pytgcalls.types.input_stream.quality import HighQualityAudio

# --- RENDER DUMMY SERVER (Keep Alive) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Ghost Glitcher is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIG FROM RENDER ENV VARIABLES ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8401733642)) # Default numerical ID
ADMIN_HANDLE = "@SANATANI_GOJO"

# Session Parsing (Comma separated list from Render)
SESSION_STRINGS = os.environ.get("SESSIONS", "").split(",")
SESSIONS = [s.strip() for s in SESSION_STRINGS if s.strip()]

# Databases
subscriptions = {} 
license_keys = {}  

# Clients Setup
clients = []
call_apps = []

for i, s in enumerate(SESSIONS):
    c = Client(f"ghost_{i}", API_ID, API_HASH, session_string=s)
    clients.append(c)
    call_apps.append(PyTgCalls(c))

# --- HELPERS ---
def is_subscribed(user_id):
    if user_id == ADMIN_ID: return True
    if user_id in subscriptions:
        if datetime.now() < subscriptions[user_id]: return True
    return False

# --- COMMANDS ---
@clients[0].on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply(
        f"🚀 **Ghost VC Glitcher Premium**\n\n"
        f"Admin: {ADMIN_HANDLE}\n"
        "Commands:\n"
        "▶️ `/glitch` - Start VC Lag\n"
        "▶️ `/stop` - Stop Glitch\n"
        "▶️ `/redeem [Code]` - Activate Plan\n"
        "▶️ `/gen` - (Admin Only) Create Key"
    )

@clients[0].on_message(filters.command("gen") & filters.user(ADMIN_ID))
async def generate_key(client, message):
    key = "GHOST-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    license_keys[key] = 30 
    await message.reply(f"🔑 **Key:** `{key}`\nValidity: 30 Days")

@clients[0].on_message(filters.command("redeem"))
async def redeem_key(client, message):
    try:
        key = message.text.split()[1]
        if key in license_keys:
            expiry = datetime.now() + timedelta(days=license_keys[key])
            subscriptions[message.from_user.id] = expiry
            del license_keys[key]
            await message.reply(f"✅ Plan Active till: `{expiry.strftime('%Y-%m-%d')}`")
        else: await message.reply("❌ Invalid Key")
    except: await message.reply("Usage: `/redeem GHOST-XXXXXX`")

@clients[0].on_message(filters.command("glitch"))
async def glitch_start(client, message):
    if not is_subscribed(message.from_user.id):
        await message.reply(f"🚫 Buy plan from {ADMIN_HANDLE}")
        return

    chat_id = message.chat.id
    msg = await message.reply("🛸 **Ghost IDs joining...**")
    
    # Heavy Payload for Glitch
    ghost_stream = "ffmpeg -f lavfi -i noise=alls:1:100 -f s16le -ac 1 -ar 48000 pipe:1"

    for app in call_apps:
        try:
            await app.join_group_call(chat_id, InputStream(ghost_stream, audio_parameters=HighQualityAudio()))
            await asyncio.sleep(0.5)
        except: continue

    await msg.edit("🔥 **VC GLITCHED SUCCESSFULLY**\nStatus: `Connecting...` (Lag Active)")

@clients[0].on_message(filters.command("stop"))
async def stop_glitch(client, message):
    if not is_subscribed(message.from_user.id): return
    for app in call_apps:
        try: await app.leave_group_call(message.chat.id)
        except: pass
    await message.reply("🛑 Stopped.")

async def start_services():
    Thread(target=run_flask).start()
    for app in call_apps: await app.start()
    await asyncio.gather(*[c.start() for c in clients])
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())
    
