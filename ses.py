import os
import time
import asyncio
import requests
from flask import Flask
from threading import Thread

# Discord yaması (READY paketindeki hatayı engeller)
import discord.state
old_parse_ready_supp = discord.state.ConnectionState.parse_ready_supplemental

def patched_parse_ready_supplemental(self, data):
    if isinstance(data, dict):
        data.pop('user_settings', None)
    return old_parse_ready_supp(self, data)

discord.state.ConnectionState.parse_ready_supplemental = patched_parse_ready_supplemental

import discord
from discord.ext import commands

# 1. Web Sunucusu
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

# 2. Self-Ping
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
                voice_client = channel.guild.voice_client
                if voice_client is None or not voice_client.is_connected():
                    if voice_client:
                        await voice_client.disconnect(force=True)
                    await channel.connect(self_deaf=True, self_mute=True)
                else:
                    if voice_client.channel.id != channel.id:
                        await voice_client.move_to(channel)
        except Exception as e:
            print(f"Hata: {e}")
        await asyncio.sleep(15)

@bot.event
async def on_ready():
    print(f"Giriş yapıldı: {bot.user}")
    bot.loop.create_task(maintain_voice_connection())

if __name__ == "__main__":
    keep_alive()
    start_self_ping()
    bot.run(TOKEN, reconnect=True)
