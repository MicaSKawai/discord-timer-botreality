import discord
from discord.ext import commands
import asyncio
import os
import json
from datetime import datetime, timedelta

TOKEN = os.getenv("DISCORD_TOKEN")

CANAL_AVISOS = 1481166318026752133
CANAL_REGISTRO = 1481166533748326421

DATA_FILE = "data.json"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- DATA ---------------- #

def cargar_datos():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def guardar_datos(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

timers = cargar_datos()

# ---------------- TIMER SYSTEM ---------------- #

async def iniciar_timer(timer):

    ahora = datetime.utcnow().timestamp()
    espera = timer["fin"] - ahora

    if espera > 0:
        await asyncio.sleep(espera)

    canal = bot.get_channel(CANAL_AVISOS)
    user = await bot.fetch_user(timer["usuario"])

    embed = discord.Embed(
        title="⏰ Timer terminado",
        description=timer["mensaje"],
        color=discord.Color.green()
    )

    if timer["everyone"]:
        await canal.send(f"{user.mention} @everyone", embed=embed)
    else:
        await canal.send(f"{user.mention}", embed=embed)

    timers.remove(timer)
    guardar_datos(timers)

async def crear_timer(ctx, nombre, horas, mensaje, everyone=True):

    ahora = datetime.utcnow()
    fin = ahora + timedelta(hours=horas)

    timer = {
        "usuario": ctx.author.id,
        "nombre": nombre,
        "fin": fin.timestamp(),
        "mensaje": mensaje,
        "everyone": everyone
    }

    timers.append(timer)
    guardar_datos(timers)

    embed = discord.Embed(
        title=f"✅ Timer iniciado: {nombre}",
        color=discord.Color.blue()
    )

    embed.add_field(name="Usuario", value=ctx.author.mention)
    embed.add_field(name="Inicio", value=ahora.strftime("%H:%M:%S"))
    embed.add_field(name="Fin", value=fin.strftime("%H:%M:%S"))

    await ctx.send(embed=embed)

    bot.loop.create_task(iniciar_timer(timer))

# ---------------- BOTONES ---------------- #

class PanelTimers(discord.ui.View):

    @discord.ui.button(label="📦 Cajas", style=discord.ButtonStyle.primary)
    async def cajas(self, interaction: discord.Interaction, button: discord.ui.Button):
        await crear_timer(interaction, "Cajas", 3, "📦 Ya puedes recoger cajas!")

    @discord.ui.button(label="🧔 Capataz", style=discord.ButtonStyle.success)
    async def capataz(self, interaction: discord.Interaction, button: discord.ui.Button):
        await crear_timer(interaction, "Capataz", 5, "🧔 El capataz tiene nueva misión!")

    @discord.ui.button(label="💰 Robo", style=discord.ButtonStyle.danger)
    async def robo(self, interaction: discord.Interaction, button: discord.ui.Button):
        await crear_timer(interaction, "Robo", 2, "💰 Ya puedes robar otra propiedad!")

# ---------------- READY ---------------- #

@bot.event
async def on_ready():

    print(f"Bot conectado como {bot.user}")

    for timer in timers:
        bot.loop.create_task(iniciar_timer(timer))

# ---------------- COMANDOS ---------------- #

@bot.command()
async def panel(ctx):

    embed = discord.Embed(
        title="🎮 Panel de timers",
        description="Usa los botones para iniciar timers",
        color=discord.Color.gold()
    )

    await ctx.send(embed=embed, view=PanelTimers())

@bot.command()
async def cajas(ctx):

    if ctx.channel.id != CANAL_REGISTRO:
        return

    await crear_timer(
        ctx,
        "Cajas",
        3,
        "📦 Ya puedes recoger tu cargamento de cajas!"
    )

@bot.command()
async def capataz(ctx):

    if ctx.channel.id != CANAL_REGISTRO:
        return

    await crear_timer(
        ctx,
        "Capataz",
        5,
        "🧔 El capataz tiene una nueva misión!"
    )

@bot.command()
async def robo(ctx):

    if ctx.channel.id != CANAL_REGISTRO:
        return

    await crear_timer(
        ctx,
        "Robo",
        2,
        "💰 Ya puedes robar otra propiedad!"
    )

@bot.command()
async def cargas(ctx):

    if ctx.channel.id != CANAL_REGISTRO:
        return

    await crear_timer(
        ctx,
        "Cargas",
        72,
        "🚛 VE A COMPRAR CARGADORES CON TODOS TUS PJs!",
        everyone=False
    )

@bot.command()
async def prueba(ctx):

    if ctx.channel.id != CANAL_REGISTRO:
        return

    ahora = datetime.utcnow()
    fin = ahora + timedelta(minutes=5)

    timer = {
        "usuario": ctx.author.id,
        "nombre": "Prueba",
        "fin": fin.timestamp(),
        "mensaje": "🧪 Timer de prueba terminado!",
        "everyone": True
    }

    timers.append(timer)
    guardar_datos(timers)

    embed = discord.Embed(
        title="🧪 Timer de prueba iniciado",
        color=discord.Color.orange()
    )

    embed.add_field(name="Fin", value=fin.strftime("%H:%M:%S"))

    await ctx.send(embed=embed)

    bot.loop.create_task(iniciar_timer(timer))

@bot.command()
async def timers(ctx):

    if not timers:
        await ctx.send("No hay timers activos.")
        return

    embed = discord.Embed(
        title="⏳ Timers activos",
        color=discord.Color.purple()
    )

    for t in timers:

        user = await bot.fetch_user(t["usuario"])
        tiempo = datetime.fromtimestamp(t["fin"])

        embed.add_field(
            name=t["nombre"],
            value=f"{user.name} → {tiempo.strftime('%d/%m %H:%M')}",
            inline=False
        )

    await ctx.send(embed=embed)

@bot.command()
async def mistimers(ctx):

    embed = discord.Embed(
        title="🧾 Tus timers",
        color=discord.Color.blue()
    )

    found = False

    for t in timers:

        if t["usuario"] == ctx.author.id:

            tiempo = datetime.fromtimestamp(t["fin"])

            embed.add_field(
                name=t["nombre"],
                value=f"Termina → {tiempo.strftime('%d/%m %H:%M')}",
                inline=False
            )

            found = True

    if not found:
        await ctx.send("No tienes timers activos.")
        return

    await ctx.send(embed=embed)

bot.run(TOKEN)
