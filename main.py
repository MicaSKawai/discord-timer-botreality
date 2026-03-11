import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

TOKEN = os.getenv("DISCORD_TOKEN")

# ----- WEB SERVER PARA RAILWAY -----

app = Flask('')

@app.route('/')
def home():
    return "Bot online"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ----- BOT DISCORD -----

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Bot funcionando")

# iniciar webserver
keep_alive()

# iniciar bot
bot.run(TOKEN)
