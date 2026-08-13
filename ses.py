import os
import time
import asyncio
import requests
from flask import Flask
from threading import Thread

# --- DISCORD READY/SETTINGS SIFIRLAMA YAMASI ---
import discord.state
import discord.settings

# Discord'un bozuk user_settings paketini bypass ediyoruz
def noop_parse_ready_supp(self, data):
    pass

discord.state.ConnectionState.parse_ready_supplemental = noop_parse_ready_supp

# Settings init hatasını tamamen bypass et
old_settings_init = discord.settings.Settings.__init__
def safe_settings_init(self, data, state):
    if not isinstance(data, dict):
        data = {}
    old_settings_init(self, data, state)

discord.settings.Settings.__init__ = safe_settings_init
# -----------------------------------------------

import discord
from discord.ext import commands

# 1. Web Sunucusu (Render'ın uyanık kalması için)
app = Flask('')

@app.route('/')
def home():
    return "Bot ses kanalında aktif!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. Self-Ping (Render uykusunu engeller)
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

# 3. Ayarlar ve Bağlantı
TOKEN = os.environ.get("TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", 0))

bot = commands.Bot(command_prefix="!", self_bot=True)

async def maintain_voice_connection():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                # Zaten ses kanalındaysa dokunma, başka kanaldaysa taşı, seste değilse bağlan
                if bot.voice_clients:
                    vc = bot.voice_clients[0]
                    if vc.channel.id != CHANNEL_ID:
                        await vc.move_to(channel)
                else:
                    await channel.connect(self_deaf=True, self_mute=True)
            else:
                print("HATA: CHANNEL_ID bulunamadı veya yan hesabın kanala erişim yetkisi yok!")
        except Exception as e:
            print(f"Ses bağlantı hatası: {e}")
        await asyncio.sleep(30)  # 30 saniyede bir kontrol et

@bot.event
async def on_ready():
    print(f"Giriş yapıldı: {bot.user}")
    bot.loop.create_task(maintain_voice_connection())

if __name__ == "__main__":
    keep_alive()
    start_self_ping()
    bot.run(TOKEN, reconnect=True)
