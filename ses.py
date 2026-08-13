import os
import time
import asyncio
import requests
from flask import Flask
from threading import Thread

# --- READY HATASINI GEÇİREN YAMA ---
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
# -----------------------------------

import discord

# 1. Web Sunucusu
app = Flask('')

@app.route('/')
def home():
    return "Aktif"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

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

def start_self_ping():
    t = Thread(target=self_ping_loop)
    t.daemon = True
    t.start()

# 3. İstemci Tanımlama (commands.Bot DEĞİL, Saf Client)
TOKEN = os.environ.get("TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", 0))

client = discord.Client(self_bot=True)

# Mesaj dinlemeyi tamamen kapatıyoruz ki o AttributeError hatası imkansız olsun
async def on_message(message):
    pass
client.on_message = on_message

async def voice_loop():
    await client.wait_until_ready()
    print(f"GIRIS YAPILDI: {client.user}")
    
    while not client.is_closed():
        try:
            channel = client.get_channel(CHANNEL_ID)
            if channel:
                # Zaten herhangi bir ses kanalındaysa işlem yapma
                if not client.voice_clients:
                    print(f"Sese baglaniliyor: {channel.name}")
                    await channel.connect(self_deaf=True, self_mute=True)
                else:
                    vc = client.voice_clients[0]
                    if vc.channel.id != CHANNEL_ID:
                        print("Farkli kanalda, hedefe tasiniyor...")
                        await vc.move_to(channel)
            else:
                print("HATA: CHANNEL_ID bulunamadi veya kanala erişim yetkisi yok!")
        except Exception as e:
            print(f"Ses baglanti hatasi: {e}")
            
        await asyncio.sleep(20)

@client.event
async def on_ready():
    client.loop.create_task(voice_loop())

if __name__ == "__main__":
    keep_alive()
    start_self_ping()
    client.run(TOKEN, reconnect=True)
