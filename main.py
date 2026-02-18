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

# --- RENDER DUMMY SERVER ---
app = Flask(__name__)
@app.route('/')
def home(): return "Ghost Glitcher with Bot Token is Online!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- CONFIG FROM RENDER ---
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "") # <--- Naya Variable
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8401733642))
ADMIN_HANDLE = "@SANATANI_GOJO"

# Session Parsing
SESSION_STRINGS = os.environ.get("SESSIONS", "").split(",")
SESSIONS = [s.strip() for s in SESSION_STRINGS if s.strip()]

# 1. Main Bot Client (Interface ke liye)
bot = Client("glitch_bot", API_ID, API_HASH, bot_token=BOT_TOKEN)

# 2. Helper Userbot Clients (Glitch karne ke liye)
userbots = []
call_apps = []

for i, s in enumerate(SESSIONS):
    ub = Client(f"ghost_{i}", API_ID, API_HASH, session_string=s)
    userbots.append(ub)
    call_apps.append(PyTgCalls(ub))

# --- DATABASE ---
subscriptions = {} 
license_keys = {}  

# --- HELPERS ---
def is_subscribed(user_id):
    if user_id == ADMIN_ID: return True
    return user_id in subscriptions and datetime.now() < subscriptions[user_id]

# --- BOT COMMANDS ---

@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply(
        f"🛸 **Welcome to Ghost VC Glitcher**\n\n"
        f"Admin: {ADMIN_HANDLE}\n"
        "Use `/glitch [Group Link/ID]` to start lag."
    )

@bot.on_message(filters.command("gen") & filters.user(ADMIN_ID))
async def generate_key(client, message):
    key = "GHOST-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    license_keys[key] = 30 
    await message.reply(f"🔑 **Key Generated:** `{key}`")

@bot.on_message(filters.command("redeem"))
async def redeem_key(client, message):
    try:
        key = message.text.split()[1]
        if key in license_keys:
            subscriptions[message.from_user.id] = datetime.now() + timedelta(days=30)
            del license_keys[key]
            await message.reply("✅ Premium Activated for 30 Days!")
        else: await message.reply("❌ Invalid Key")
    except: await message.reply("Usage: `/redeem GHOST-XXXXXX`")

@bot.on_message(filters.command("glitch"))
async def glitch_start(client, message):
    if not is_subscribed(message.from_user.id):
        await message.reply(f"🚫 No Subscription! Buy from {ADMIN_HANDLE}")
        return

    try:
        target = message.text.split()[1] # Link ya Chat ID
    except:
        await message.reply("❌ Usage: `/glitch @group_username` or `/glitch chat_id`")
        return

    msg = await message.reply("⚡ **Ghost IDs are infiltrating the VC...**")
    
    ghost_payload = "ffmpeg -f lavfi -i noise=alls:1:100 -f s16le -ac 1 -ar 48000 pipe:1"

    success = 0
    for app in call_apps:
        try:
            await app.join_group_call(target, InputStream(ghost_payload, audio_parameters=HighQualityAudio()))
            success += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Join Error: {e}")

    await msg.edit(f"🔥 **Glitch Sent!**\nConnected: `{success}/{len(SESSIONS)}` IDs\nTarget: `{target}`")

@bot.on_message(filters.command("stop"))
async def stop_glitch(client, message):
    if not is_subscribed(message.from_user.id): return
    target = message.text.split()[1]
    for app in call_apps:
        try: await app.leave_group_call(target)
        except: pass
    await message.reply("🛑 Stopped.")

# --- STARTUP ---
async def start_services():
    Thread(target=run_flask).start()
    
    # Start Bot & Userbots
    await bot.start()
    for i, ub in enumerate(userbots):
        await ub.start()
        await call_apps[i].start()
    
    print("SYSTEMS ONLINE!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_services())
