import discord
from discord.ext import commands
import os

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise Exception("ERROR: No se encontró la variable TOKEN en Railway")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("pong")

bot.run(TOKEN)
