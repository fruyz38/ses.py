import os
import time
import asyncio
import logging
import requests
from flask import Flask
from threading import Thread

logging.basicConfig(level=logging.INFO)

import discord
import discord.state
import discord.settings
import discord.utils

# ==================== KULLANICI AYARLARI ====================
CHANNEL_ID = 1533212315355316227
# ============================================================

# --- 1. BUILD NUMBER & BROWSER VERSION YAMASI ---
async def fake_async_build_number(*args, **kwargs):
    return 315682

async def fake_async_browser_version(*args, **kwargs):
    return "128.0.0.0"

discord.utils.get_build_number = fake_async_build_number
discord.utils.get_browser_version = fake_async_browser_version

if hasattr(discord.utils, '_get_build_number'):
    discord.utils._get_build_number = fake_async_build_number
if hasattr(discord.utils, '_get_browser_version'):
    discord.utils._get_browser_version = fake_async_browser_version

# --- 2. GATEWAY READY YAMASI ---
async def dummy_parse_ready_supp(self, data):
    pass

def noop_parse_ready_supp(self, data):
    pass

discord.state.ConnectionState.parse_ready_supplemental = noop_parse_ready_supp
discord.state.ConnectionState._parse_ready_supplemental = dummy_parse_ready_supp

old_settings_init = discord.settings.Settings.__init__
def safe_settings_init(self, data, state):
    if not isinstance(data, dict):
        data = {}
    old_settings_init(self, data, state)

discord.settings.Settings.__init__ = safe_settings_init
# -------------------------------------------------------------

app = Flask('')

@app.route('/')
def home():
    return "Bot Aktif!"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def self_ping_loop():
    url = os.environ.get("RENDER_EXTERNAL_URL")
    if url:
        while True:
            try:
                time.sleep(240)
                requests.get(url)
            except Exception:
                pass

TOKEN = os.environ.get("TOKEN")

client = discord.Client(self_bot=True)

async def on_message(message):
    pass
client.on_message = on_message

async def voice_loop():
    await client.wait_until_ready()
    print(f"\n==========================================", flush=True)
    print(f"GİRİŞ BAŞARILI: {client.user}", flush=True)
    print(f"==========================================\n", flush=True)
    
    while not client.is_closed():
        try:
            # Önce önbellekten dene, bulamazsa Discord API'den zorla çek (fetch)
            channel = client.get_channel(CHANNEL_ID)
            if not channel:
                try:
                    channel = await client.fetch_channel(CHANNEL_ID)
                except Exception as fetch_err:
                    print(f"Kanal fetch edilemedi: {fetch_err}", flush=True)

            if channel:
                if not client.voice_clients:
                    print(f"Sese baglaniliyor: {channel.name} (ID: {CHANNEL_ID})", flush=True)
                    await channel.connect(self_deaf=True, self_mute=True)
                    print(">>> SESE BAŞARIYLA GİRİLDİ! <<<", flush=True)
                else:
                    vc = client.voice_clients[0]
                    if vc.channel.id != CHANNEL_ID:
                        print("Farkli kanalda, hedefe tasiniyor...", flush=True)
                        await vc.move_to(channel)
            else:
                print(f"HATA: CHANNEL_ID ({CHANNEL_ID}) bulunamadi! Hesabın bu kanala erişimi/yetkisi olduğundan emin ol.", flush=True)
        except Exception as e:
            print(f"Ses baglanti hatasi: {e}", flush=True)
            
        await asyncio.sleep(15)

@client.event
async def on_ready():
    print("Discord baglantisi kuruldu, ses döngüsü baslatiliyor...", flush=True)
    client.loop.create_task(voice_loop())

if __name__ == "__main__":
    print("=== SİSTEM BAŞLATILIYOR ===", flush=True)
    
    t_flask = Thread(target=run_flask)
    t_flask.daemon = True
    t_flask.start()

    t_ping = Thread(target=self_ping_loop)
    t_ping.daemon = True
    t_ping.start()

    if not TOKEN:
        print("KRİTİK HATA: Render variables kısmında TOKEN bulunamadı!", flush=True)
    else:
        print("Token okundu, Discord'a baglanilmaya calisiliyor...", flush=True)
        client.run(TOKEN, reconnect=True)
