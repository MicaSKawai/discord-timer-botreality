import discord
from discord.ext import commands, tasks
import sqlite3
import time
import os
from datetime import datetime
import threading
from flask import Flask

# ---------------- KEEP ALIVE (ANTI SLEEP) ----------------

app = Flask('')

@app.route('/')
def home():
    return "Bot activo"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

keep_alive()

# ---------------- TOKEN ----------------

TOKEN = os.environ["DISCORD_TOKEN"]

# ---------------- CANALES ----------------

CANAL_AVISOS = 1481166318026752133
CANAL_REGISTRO = 1481166533748326421

# ---------------- DISCORD SETUP ----------------

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- DATABASE ----------------

db = sqlite3.connect("timers.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS timers(
user_id INTEGER,
username TEXT,
tipo TEXT,
inicio INTEGER,
fin INTEGER
)
""")

db.commit()

# ---------------- FUNCIONES ----------------

def ahora():
    return int(time.time())

def formatear_hora(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")

def tiempo_restante(seg):

    horas = seg // 3600
    minutos = (seg % 3600) // 60

    if horas > 0:
        return f"{horas}h {minutos}m"
    else:
        return f"{minutos}m"

# ---------------- CREAR TIMER ----------------

async def iniciar_timer(ctx, tipo, horas):

    if ctx.channel.id != CANAL_REGISTRO:
        return

    inicio = ahora()
    fin = inicio + int(horas * 3600)

    cursor.execute(
        "INSERT INTO timers VALUES (?,?,?,?,?)",
        (ctx.author.id, ctx.author.name, tipo, inicio, fin)
    )

    db.commit()

    embed = discord.Embed(
        title="⏱️ Timer iniciado",
        color=0x00ffaa
    )

    embed.add_field(name="Usuario", value=ctx.author.mention, inline=False)
    embed.add_field(name="Acción", value=tipo, inline=True)
    embed.add_field(name="Duración", value=f"{horas} horas", inline=True)
    embed.add_field(name="Inicio", value=formatear_hora(inicio), inline=True)
    embed.add_field(name="Finaliza", value=formatear_hora(fin), inline=True)

    await ctx.send(embed=embed)

# ---------------- COMANDOS ----------------

@bot.command()
async def cajas(ctx):
    await iniciar_timer(ctx, "Cajas", 3)

@bot.command()
async def capataz(ctx):
    await iniciar_timer(ctx, "Capataz", 5)

@bot.command()
async def robo(ctx):
    await iniciar_timer(ctx, "Robo", 2)

@bot.command()
async def cargas(ctx):
    await iniciar_timer(ctx, "Cargas", 72)

# TIMER DE PRUEBA (1 MINUTO)

@bot.command()
async def test(ctx):
    await iniciar_timer(ctx, "Test", 0.0167)

# ---------------- VER TODOS LOS TIMERS ----------------

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

        restante = t[4] - ahora()

        if restante < 0:
            restante = 0

        embed.add_field(
            name=f"{t[2]} • {t[1]}",
            value=f"⏳ {tiempo_restante(restante)} restantes\n🕒 Fin: {formatear_hora(t[4])}",
            inline=False
        )

    await ctx.send(embed=embed)

# ---------------- VER MIS TIMERS ----------------

@bot.command()
async def mistimers(ctx):

    cursor.execute("SELECT * FROM timers WHERE user_id=?", (ctx.author.id,))
    datos = cursor.fetchall()

    if not datos:
        await ctx.send("No tienes timers activos.")
        return

    embed = discord.Embed(
        title="📊 Tus timers activos",
        color=0x9b59b6
    )

    for t in datos:

        restante = t[4] - ahora()

        if restante < 0:
            restante = 0

        embed.add_field(
            name=f"{t[2]}",
            value=f"⏳ {tiempo_restante(restante)} restantes\n🕒 Fin: {formatear_hora(t[4])}",
            inline=False
        )

    await ctx.send(embed=embed)

# ---------------- REVISAR TIMERS ----------------

@tasks.loop(seconds=30)
async def revisar():

    cursor.execute("SELECT * FROM timers WHERE fin <= ?", (ahora(),))
    lista = cursor.fetchall()

    if not lista:
        return

    canal = bot.get_channel(CANAL_AVISOS)

    for t in lista:

        user = await bot.fetch_user(t[0])
        tipo = t[2]

        if tipo == "Cajas":
            msg = f"{user.mention} @everyone Ya puedes recoger tu cargamento de cajas!!"

        elif tipo == "Capataz":
            msg = f"{user.mention} @everyone Ya está listo el capataz para entregarte una nueva misión!!"

        elif tipo == "Robo":
            msg = f"{user.mention} @everyone Ya puedes robar otra propiedad! Ponte la máscara, toma tu uzi y ve a divertirte mi farmero favorito!"

        elif tipo == "Cargas":
            msg = f"{user.mention} VE A COMPRAR CARGADORES CON TODOS TUS PJs Farmero de corazón!!"

        elif tipo == "Test":
            msg = f"{user.mention} ⏰ Timer de prueba finalizado!"

        else:
            msg = f"{user.mention} Timer terminado!"

        embed = discord.Embed(
            title="✅ Timer finalizado",
            description=msg,
            color=0x00ff00
        )

        embed.add_field(name="Acción", value=tipo)

        await canal.send(embed=embed)

        cursor.execute(
            "DELETE FROM timers WHERE user_id=? AND tipo=? AND inicio=? AND fin=?",
            (t[0], t[2], t[3], t[4])
        )

        db.commit()

# ---------------- BOT READY ----------------

@bot.event
async def on_ready():
    print("Bot conectado como", bot.user)
    revisar.start()

bot.run(TOKEN)
