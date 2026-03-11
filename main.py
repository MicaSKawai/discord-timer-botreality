import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import sqlite3
import datetime
import asyncio

load_dotenv()
TOKEN = os.getenv("TOKEN")

CANAL_AVISOS = 1481166318026752133
CANAL_REGISTRO = 1481166533748326421

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Base de datos
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

def tiempo_actual():
    return int(datetime.datetime.now().timestamp())

def crear_embed_inicio(usuario, accion, horas):
    embed = discord.Embed(
        title=f"⏱️ Timer iniciado: {accion}",
        description=f"{usuario.mention} inició **{accion}**",
        color=0x00ffcc
    )

    embed.add_field(name="Hora", value=hora_actual(), inline=True)
    embed.add_field(name="Duración", value=f"{horas} horas", inline=True)
    embed.set_footer(text="Sistema de timers")

    return embed

def crear_embed_fin(usuario, accion, mensaje):
    embed = discord.Embed(
        title=f"✅ Timer terminado: {accion}",
        description=f"{usuario.mention}\n{mensaje}",
        color=0x00ff00
    )

    embed.set_footer(text="Sistema de timers")

    return embed

async def iniciar_timer(ctx, nombre, horas, mensaje_final, everyone=True):

    if ctx.channel.id != CANAL_REGISTRO:
        return

    fin = tiempo_actual() + horas * 3600

    cursor.execute(
        "INSERT INTO timers VALUES (?,?,?,?)",
        (ctx.author.id, ctx.author.name, nombre, fin)
    )
    db.commit()

    embed = crear_embed_inicio(ctx.author, nombre, horas)
    await ctx.send(embed=embed)

@bot.command()
async def cajas(ctx):
    await iniciar_timer(
        ctx,
        "Cajas",
        3,
        "Ya puedes recoger tu cargamento de cajas!",
        True
    )

@bot.command()
async def capataz(ctx):
    await iniciar_timer(
        ctx,
        "Capataz",
        5,
        "Ya está listo el capataz para entregarte una nueva misión!",
        True
    )

@bot.command()
async def robo(ctx):
    await iniciar_timer(
        ctx,
        "Robo",
        2,
        "Ya puedes robar otra propiedad! Ponte la máscara y toma tu Uzi 😈",
        True
    )

@bot.command()
async def cargas(ctx):
    await iniciar_timer(
        ctx,
        "Cargas",
        72,
        "VE A COMPRAR CARGADORES CON TODOS TUS PJs Farmero de corazón!",
        False
    )

@bot.command()
async def prueba(ctx):
    if ctx.channel.id != CANAL_REGISTRO:
        return

    fin = tiempo_actual() + 300

    cursor.execute(
        "INSERT INTO timers VALUES (?,?,?,?)",
        (ctx.author.id, ctx.author.name, "Prueba", fin)
    )
    db.commit()

    embed = discord.Embed(
        title="🧪 Timer de prueba iniciado",
        description=f"{ctx.author.mention} inició un timer de **5 minutos**",
        color=0x00ffff
    )

    await ctx.send(embed=embed)

@bot.command()
async def timers(ctx):

    cursor.execute("SELECT * FROM timers")
    datos = cursor.fetchall()

    if not datos:
        await ctx.send("No hay timers activos.")
        return

    embed = discord.Embed(
        title="📊 Timers activos",
        color=0x3498db
    )

    for t in datos:

        restante = t[3] - tiempo_actual()

        if restante < 0:
            restante = 0

        minutos = int(restante / 60)

        embed.add_field(
            name=f"{t[2]} - {t[1]}",
            value=f"{minutos} minutos restantes",
            inline=False
        )

    await ctx.send(embed=embed)

@tasks.loop(seconds=30)
async def revisar_timers():

    ahora = tiempo_actual()

    cursor.execute("SELECT * FROM timers WHERE fin <= ?", (ahora,))
    terminados = cursor.fetchall()

    if not terminados:
        return

    canal = bot.get_channel(CANAL_AVISOS)

    for t in terminados:

        user_id = t[0]
        tipo = t[2]

        usuario = await bot.fetch_user(user_id)

        if tipo == "Cajas":
            mensaje = f"{usuario.mention} @everyone Ya puedes recoger tu cargamento de cajas!"
        elif tipo == "Capataz":
            mensaje = f"{usuario.mention} @everyone Ya está listo el capataz para entregarte una nueva misión!"
        elif tipo == "Robo":
            mensaje = f"{usuario.mention} @everyone Ya puedes robar otra propiedad!"
        elif tipo == "Cargas":
            mensaje = f"{usuario.mention} VE A COMPRAR CARGADORES CON TODOS TUS PJs Farmero!"
        elif tipo == "Prueba":
            mensaje = f"{usuario.mention} @everyone Timer de prueba terminado!"
        else:
            mensaje = f"{usuario.mention} tu timer terminó."

        embed = crear_embed_fin(usuario, tipo, mensaje)

        await canal.send(embed=embed)

        cursor.execute("DELETE FROM timers WHERE user_id=? AND tipo=? AND fin=?", (t[0], t[2], t[3]))
        db.commit()

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    revisar_timers.start()

bot.run(TOKEN)
