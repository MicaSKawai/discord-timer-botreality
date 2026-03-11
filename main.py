import os
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

if TOKEN is None:
    raise Exception("ERROR: No se encontró la variable DISCORD_TOKEN en Railway")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! El bot funciona.")

bot.run(TOKEN)
