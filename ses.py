import os
import time
import asyncio
import requests
from flask import Flask
from threading import Thread

# --- DISCORD READY YAMASI ---
import discord.state
import discord.settings

def noop_parse_ready_supp(self, data):
    pass

discord.state.ConnectionState.parse_ready_supplemental = noop_parse_ready_supp

old_settings_init = discord.settings.Settings.__init__
def safe_settings_init(self, data, state):
    if not isinstance(data, dict):
        data = {}
    old_settings_init(self, data, state)

discord.settings.Settings.__init__ = safe_settings_init
# ----------------------------

import discord

# 1. Web Sunucusu
app = Flask('')

@app.route('/')
def home():
    return "Aktif"

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Self Ping
def self_ping_loop():
    url = os.environ.get("RENDER_EXTERNAL_URL")
    if url:
        while True:
            try:
                time.sleep(240)
                requests.get(url)
            except:
                pass

# 3. İstemci Tanımlama
TOKEN = os.environ.get("TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", 0))

client = discord.Client(self_bot=True)

# Mesaj dinlemeyi tamamen eziyoruz
async def on_message(message):
    pass
client.on_message = on_message

async def voice_loop():
    await client.wait_until_ready()
    print(f"GIRIS YAPILDI: {client.user}", flush=True)
    
    while not client.is_closed():
        try:
            channel = client.get_channel(CHANNEL_ID)
            if channel:
                if not client.voice_clients:
                    print(f"Sese baglaniliyor: {channel.name}", flush=True)
                    await channel.connect(self_deaf=True, self_mute=True)
                else:
                    vc = client.voice_clients[0]
                    if vc.channel.id != CHANNEL_ID:
                        print("Farkli kanalda, hedefe tasiniyor...", flush=True)
                        await vc.move_to(channel)
            else:
                print("HATA: CHANNEL_ID bulunamadi veya kanala erişim yetkisi yok!", flush=True)
        except Exception as e:
            print(f"Ses baglanti hatasi: {e}", flush=True)
            
        await asyncio.sleep(20)

@client.event
async def on_ready():
    client.loop.create_task(voice_loop())

if __name__ == "__main__":
    # Flask sunucusunu kesinlikle arka planda (Daemon Thread) başlatıyoruz
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Self-ping thread
    t_ping = Thread(target=self_ping_loop)
    t_ping.daemon = True
    t_ping.start()

    # Ana thread'i tamamen Discord Client'a veriyoruz
    client.run(TOKEN, reconnect=True)
