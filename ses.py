import os
import time
import asyncio
import requests
from flask import Flask
from threading import Thread
import discord

# 1. Flask Web Servisi (Render'ın port isteğini karşılamak için)
app = Flask('')

@app.route('/')
def home():
    return "Bot aktif ve ses kanalında nöbette!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 2. Kodun İçinden Kendi Kendine Ping Atma Mekanizması (UptimeRobot'a gerek kalmaz)
def self_ping_loop():
    # Render, projenin canlı URL'sini bu değişkene otomatik atar
    url = os.environ.get("RENDER_EXTERNAL_URL")
    
    if url:
        print(f"Self-ping sistemi aktif! Hedef: {url}")
        while True:
            try:
                # Render 15 dakikada bir uyur, her 4 dakikada bir kendine istek atalım
                time.sleep(240)
                response = requests.get(url)
                print(f"Self-ping başarılı! Durum kodu: {response.status_code}")
            except Exception as e:
                print(f"Self-ping atılırken hata oluştu: {e}")
    else:
        print("RENDER_EXTERNAL_URL bulunamadı, self-ping çalıştırılamadı.")

def start_self_ping():
    t = Thread(target=self_ping_loop)
    t.daemon = True
    t.start()

# 3. Discord Self-Bot Ayarları
TOKEN = os.environ.get("MTUzNzI2MzQ3NTY2NjA1OTI5NA.GGORl0.xIcnJz6xwaeUqqs3DWGRq4rR3qsHpz5su3tyPA")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", 0))

client = discord.Client()

async def maintain_voice_connection():
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            channel = client.get_channel(CHANNEL_ID)
            if channel:
                voice_client = channel.guild.voice_client
                
                if voice_client is None or not voice_client.is_connected():
                    print(f"[{channel.name}] kanalına bağlanılıyor...")
                    if voice_client:
                        await voice_client.disconnect(force=True)
                    
                    await channel.connect(self_deaf=True, self_mute=True)
                    print("Başarıyla ses kanalına girildi ve kilitlendi!")
                else:
                    if voice_client.channel.id != channel.id:
                        await voice_client.move_to(channel)
            else:
                print(f"Hata: {CHANNEL_ID} ID'li kanal bulunamadı!")
        except Exception as e:
            print(f"Ses bağlantı döngüsünde hata: {e}")
        
        await asyncio.sleep(15)

@client.event
async def on_ready():
    print(f"Giriş yapıldı: {client.user} (ID: {client.user.id})")
    client.loop.create_task(maintain_voice_connection())

@client.event
async def on_disconnect():
    print("Discord bağlantısı koptu, yeniden bağlanılıyor...")

if __name__ == "__main__":
    # Flask web sunucusunu başlat
    keep_alive()
    
    # Kendi kendine ping atma döngüsünü arka planda başlat
    start_self_ping()
    
    # Botu başlat
    try:
        client.run(TOKEN, reconnect=True)
    except Exception as e:
        print(f"Kritik Bot Hatası: {e}")