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

# --- RENDER DUMMY SERVER (Port Fix) ---
app = Flask(__name__)
@app.route('/')
def home(): return "Ghost Glitch Bot is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURATION ---
API_ID = 1234567 # Apna API ID yahan dalo
API_HASH = "your_api_hash_here" # Apna API Hash yahan dalo
ADMIN_ID = 8401733642 # Tumhari Numerical ID
ADMIN_HANDLE = "@SANATANI_GOJO"

# Databases
subscriptions = {} # {user_id: expiry_datetime}
license_keys = {}  # {key: days}

# IDs Sessions (Add your 5 sessions here)
SESSIONS = [
    "session_1_here",
    "session_2_here",
    "session_3_here",
    "session_4_here",
    "session_5_here"
]

# Clients Setup
clients = [Client(f"ghost_{i}", API_ID, API_HASH, session_string=s) for i, s in enumerate(SESSIONS)]
call_apps = [PyTgCalls(c) for c in clients]

# --- SUBSCRIPTION HELPERS ---
def is_subscribed(user_id):
    if user_id == ADMIN_ID: return True
    if user_id in subscriptions:
        if datetime.now() < subscriptions[user_id]:
            return True
    return False

# --- COMMANDS ---

@clients[0].on_message(filters.command("start"))
async def start_cmd(client, message):
    text = (
        "🚀 **Welcome to Ghost VC Glitcher**\n\n"
        "Status: `Premium System Active`\n"
        f"Admin: {ADMIN_HANDLE}\n\n"
        "Commands:\n"
        "▶️ `/glitch [Link]` - Start Glitch\n"
        "▶️ `/redeem [Code]` - Activate License\n"
        "▶️ `/gen` - (Admin Only) Generate Key"
    )
    await message.reply(text)

@clients[0].on_message(filters.command("gen") & filters.user(ADMIN_ID))
async def generate_key(client, message):
    key = "GHOST-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    license_keys[key] = 30 # 30 Days default
    await message.reply(f"🔑 **Generated Key:** `{key}`\nValidity: 30 Days\n\nSend this to the user.")

@clients[0].on_message(filters.command("redeem"))
async def redeem_key(client, message):
    try:
        key = message.text.split()[1]
        if key in license_keys:
            days = license_keys[key]
            expiry = datetime.now() + timedelta(days=days)
            subscriptions[message.from_user.id] = expiry
            del license_keys[key]
            await message.reply(f"✅ **Success!**\nYour plan is active until: `{expiry.strftime('%Y-%m-%d')}`")
        else:
            await message.reply("❌ Invalid or Expired Key.")
    except:
        await message.reply("❓ Usage: `/redeem GHOST-XXXXXX`")

@clients[0].on_message(filters.command("glitch"))
async def glitch_start(client, message):
    if not is_subscribed(message.from_user.id):
        await message.reply(f"🚫 **Access Denied!**\nBuy premium from {ADMIN_HANDLE}")
        return

    chat_id = message.chat.id
    msg = await message.reply("🛸 **Initializing Ghost IDs...**")
    
    # GHOST PACKET STREAM (The Glitch Engine)
    # Filter 'noise' generate karta hai jo VC buffer ko choke kar deta hai
    ghost_stream = "ffmpeg -f lavfi -i noise=alls:1:100 -f s16le -ac 1 -ar 48000 pipe:1"

    success_count = 0
    for app in call_apps:
        try:
            await app.join_group_call(
                chat_id,
                InputStream(ghost_stream, audio_parameters=HighQualityAudio())
            )
            success_count += 1
            await asyncio.sleep(1) # Anti-flood delay
        except:
            continue

    await msg.edit(f"🔥 **Glitch Active!**\nIDs Connected: `{success_count}/5`\nStatus: `Connecting...` (Lagging)")

@clients[0].on_message(filters.command("stop"))
async def stop_glitch(client, message):
    if not is_subscribed(message.from_user.id): return
    for app in call_apps:
        try: await app.leave_group_call(message.chat.id)
        except: pass
    await message.reply("🛑 **Glitch Stopped.**")

# --- STARTUP ---
async def start_services():
    print("Starting Flask...")
    Thread(target=run_flask).start()
    
    print("Starting Clients...")
    for app in call_apps: await app.start()
    await asyncio.gather(*[c.start() for c in clients])
    
    print("ALL SYSTEMS GO!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())
