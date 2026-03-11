import discord
from discord.ext import commands, tasks
import sqlite3
import datetime
import os

TOKEN = os.environ["TOKEN"]

CANAL_AVISOS = 1481166318026752133
CANAL_REGISTRO = 1481166533748326421

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

db = sqlite3.connect("timers.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS timers (
user_id INTEGER,
username TEXT,
tipo TEXT,
fin INTEGER
)
""")

db.commit()

def hora_actual():
    return datetime.datetime.now().strftime("%H:%M:%S")

def canal_correcto(ctx):
    return ctx.channel.id == CANAL_REGISTRO

def crear_timer(user, tipo, segundos):

    fin = int(datetime.datetime.now().timestamp()) + segundos

    cursor.execute(
        "INSERT INTO timers VALUES (?, ?, ?, ?)",
        (user.id, user.name, tipo, fin)
    )

    db.commit()

@tasks.loop(seconds=30)
async def revisar_timers():

    ahora = int(datetime.datetime.now().timestamp())

    cursor.execute("SELECT * FROM timers")
    timers = cursor.fetchall()

    canal = bot.get_channel(CANAL_AVISOS)

    for timer in timers:

        user_id, username, tipo, fin = timer

        if ahora >= fin:

            user = await bot.fetch_user(user_id)

            mensajes = {
                "cajas": "📦 Ya puedes volver a recoger tu cargamento de cajas!",
                "capataz": "👷 Ya está listo el capataz para entregarte una nueva misión!",
                "robo": "🕵️ Ya puedes robar otra propiedad!",
                "cargas": "🔋 VE A COMPRAR CARGADORES CON TODOS TUS PJs Farmero de corazón!!",
                "prueba": "🧪 Timer de prueba finalizado!"
            }

            everyone = tipo != "cargas"

            embed = discord.Embed(
                title="⏰ Timer finalizado",
                description=mensajes[tipo],
                color=discord.Color.green()
            )

            if everyone:
                await canal.send(f"@everyone <@{user_id}>", embed=embed)
            else:
                await canal.send(f"<@{user_id}>", embed=embed)

            cursor.execute("DELETE FROM timers WHERE user_id=? AND tipo=?", (user_id, tipo))
            db.commit()

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    revisar_timers.start()

async def iniciar_timer(ctx, tipo, segundos, titulo, color):

    if not canal_correcto(ctx):
        return

    crear_timer(ctx.author, tipo, segundos)

    embed = discord.Embed(
        title=titulo,
        description=f"{ctx.author.mention} lo inició a las **{hora_actual()}**",
        color=color
    )

    await ctx.send(embed=embed)

@bot.command()
async def cajas(ctx):
    await iniciar_timer(ctx, "cajas", 10800, "📦 Cajas registradas", discord.Color.blue())

@bot.command()
async def capataz(ctx):
    await iniciar_timer(ctx, "capataz", 18000, "👷 Capataz registrado", discord.Color.orange())

@bot.command()
async def robo(ctx):
    await iniciar_timer(ctx, "robo", 7200, "🕵️ Robo iniciado", discord.Color.red())

@bot.command()
async def cargas(ctx):
    await iniciar_timer(ctx, "cargas", 259200, "🔋 Cargas registradas", discord.Color.purple())

@bot.command()
async def prueba(ctx):
    await iniciar_timer(ctx, "prueba", 300, "🧪 Timer de prueba", discord.Color.gold())

@bot.command()
async def timers(ctx):

    cursor.execute("SELECT * FROM timers")
    timers = cursor.fetchall()

    embed = discord.Embed(
        title="⏳ Timers activos",
        color=discord.Color.blurple()
    )

    ahora = int(datetime.datetime.now().timestamp())

    for timer in timers:

        user_id, username, tipo, fin = timer

        restante = fin - ahora

        horas = restante // 3600
        minutos = (restante % 3600) // 60

        embed.add_field(
            name=f"{tipo.upper()} — {username}",
            value=f"⏳ {horas}h {minutos}m restantes",
            inline=False
        )

    await ctx.send(embed=embed)

bot.run(TOKEN)
