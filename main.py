import discord
from discord.ext import commands, tasks
import sqlite3
import time
import os
from datetime import datetime, timedelta
import threading
from flask import Flask

# ---------------- KEEP ALIVE ----------------

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
CANAL_DASHBOARD = 1481397540883792068

# ---------------- DISCORD ----------------

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS ranking(
user_id INTEGER,
username TEXT,
tipo TEXT,
cantidad INTEGER
)
""")

db.commit()

# ---------------- TIEMPO ----------------

def ahora():
    return int(time.time())

def hora_arg(ts):
    utc = datetime.utcfromtimestamp(ts)
    argentina = utc - timedelta(hours=3)
    return argentina.strftime("%H:%M")

def hora_hub(ts):
    utc = datetime.utcfromtimestamp(ts)
    argentina = utc - timedelta(hours=3)
    hub = argentina + timedelta(hours=3)
    return hub.strftime("%H:%M")

def tiempo_restante(seg):

    horas = seg // 3600
    minutos = (seg % 3600) // 60

    if horas > 0:
        return f"{horas}h {minutos}m"
    else:
        return f"{minutos}m"

# ---------------- BARRA PROGRESO ----------------

def barra_progreso(inicio, fin):

    total = fin - inicio
    pasado = ahora() - inicio

    if pasado < 0:
        pasado = 0

    if pasado > total:
        pasado = total

    progreso = pasado / total

    bloques = 16
    llenos = int(bloques * progreso)
    vacios = bloques - llenos

    barra = "█"*llenos + "░"*vacios
    porcentaje = int(progreso*100)

    return f"{barra} {porcentaje}%"

# ---------------- SUMAR RANKING ----------------

def sumar_ranking(user_id, username, tipo):

    cursor.execute(
    "SELECT cantidad FROM ranking WHERE user_id=? AND tipo=?",
    (user_id,tipo)
    )

    dato = cursor.fetchone()

    if dato:

        cursor.execute(
        "UPDATE ranking SET cantidad=cantidad+1 WHERE user_id=? AND tipo=?",
        (user_id,tipo)
        )

    else:

        cursor.execute(
        "INSERT INTO ranking VALUES (?,?,?,1)",
        (user_id,username,tipo)
        )

    db.commit()

# ---------------- TIMER ----------------

async def iniciar_timer(ctx,tipo,horas):

    if ctx.channel.id != CANAL_REGISTRO:
        return

    inicio = ahora()
    fin = inicio + int(horas*3600)

    cursor.execute(
    "INSERT INTO timers VALUES (?,?,?,?,?)",
    (ctx.author.id,ctx.author.name,tipo,inicio,fin)
    )

    db.commit()

    sumar_ranking(ctx.author.id,ctx.author.name,tipo)

    embed = discord.Embed(
    title="⏱ Timer iniciado",
    color=0x00ffaa
    )

    embed.add_field(name="Usuario",value=ctx.author.mention,inline=False)

    embed.add_field(name="Acción",value=tipo,inline=True)

    embed.add_field(
    name="Progreso",
    value=barra_progreso(inicio,fin),
    inline=False
    )

    embed.add_field(name="Fin ARG",value=hora_arg(fin))
    embed.add_field(name="Fin HUB",value=hora_hub(fin))

    await ctx.send(embed=embed)

# ---------------- COMANDOS ----------------

@bot.command()
async def cajas(ctx):
    await iniciar_timer(ctx,"Cajas",3)

@bot.command()
async def robo(ctx):
    await iniciar_timer(ctx,"Robo",2)

@bot.command()
async def capataz(ctx):
    await iniciar_timer(ctx,"Capataz",5)

@bot.command()
async def cargas(ctx):
    await iniciar_timer(ctx,"Cargas",72)

@bot.command()
async def test(ctx):
    await iniciar_timer(ctx,"Test",0.0167)

# ---------------- PANEL BOTONES ----------------

class Panel(discord.ui.View):

    @discord.ui.button(label="📦 Cajas",style=discord.ButtonStyle.primary)
    async def cajas(self,interaction:discord.Interaction,button:discord.ui.Button):

        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        await iniciar_timer(ctx,"Cajas",3)
        await interaction.response.defer()

    @discord.ui.button(label="💰 Robo",style=discord.ButtonStyle.danger)
    async def robo(self,interaction:discord.Interaction,button:discord.ui.Button):

        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        await iniciar_timer(ctx,"Robo",2)
        await interaction.response.defer()

    @discord.ui.button(label="👷 Capataz",style=discord.ButtonStyle.success)
    async def capataz(self,interaction:discord.Interaction,button:discord.ui.Button):

        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        await iniciar_timer(ctx,"Capataz",5)
        await interaction.response.defer()

    @discord.ui.button(label="🔫 Cargas",style=discord.ButtonStyle.secondary)
    async def cargas(self,interaction:discord.Interaction,button:discord.ui.Button):

        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        await iniciar_timer(ctx,"Cargas",72)
        await interaction.response.defer()

@bot.command()
async def panel(ctx):

    if ctx.channel.id != CANAL_REGISTRO:
        return

    embed = discord.Embed(
    title="🎮 Panel de Timers",
    description="Usa los botones para iniciar timers.",
    color=0x5865F2
    )

    await ctx.send(embed=embed,view=Panel())

# ---------------- DASHBOARD ----------------

dashboard_message=None

@bot.command()
async def dashboard(ctx):

    global dashboard_message

    if ctx.channel.id != CANAL_DASHBOARD:
        return

    embed=discord.Embed(
    title="📊 Timers activos",
    description="Panel automático",
    color=0x2ecc71
    )

    dashboard_message=await ctx.send(embed=embed)

@tasks.loop(seconds=5)
async def actualizar_dashboard():

    global dashboard_message

    if dashboard_message is None:
        return

    cursor.execute("SELECT * FROM timers")
    datos=cursor.fetchall()

    embed=discord.Embed(
    title="📊 Timers activos del servidor",
    color=0x2ecc71
    )

    if not datos:
        embed.add_field(
        name="Sin timers",
        value="Nadie tiene timers activos",
        inline=False
        )

    for t in datos:

        restante=t[4]-ahora()

        if restante<=0:
            continue

        barra=barra_progreso(t[3],t[4])

        embed.add_field(
        name=f"{t[2]} • {t[1]}",
        value=f"{barra}\n⏳ {tiempo_restante(restante)}",
        inline=False
        )

    try:
        await dashboard_message.edit(embed=embed)
    except:
        pass

# ---------------- FINALIZAR TIMERS ----------------

@tasks.loop(seconds=5)
async def revisar():

    cursor.execute("SELECT * FROM timers WHERE fin <= ?",(ahora(),))
    lista=cursor.fetchall()

    if not lista:
        return

    canal=bot.get_channel(CANAL_AVISOS)

    for t in lista:

        user=await bot.fetch_user(t[0])
        tipo=t[2]

        embed=discord.Embed(
        title="✅ Timer finalizado",
        description=f"{user.mention} tu **{tipo}** ya terminó",
        color=0x00ff00
        )

        await canal.send(embed=embed)

        cursor.execute(
        "DELETE FROM timers WHERE user_id=? AND tipo=? AND inicio=? AND fin=?",
        (t[0],t[2],t[3],t[4])
        )

        db.commit()

# ---------------- STATS USUARIO ----------------

@bot.command()
async def stats(ctx):

    cursor.execute(
    "SELECT tipo,cantidad FROM ranking WHERE user_id=?",
    (ctx.author.id,)
    )

    datos=cursor.fetchall()

    if not datos:
        await ctx.send("No tienes actividad registrada.")
        return

    embed=discord.Embed(
    title=f"📊 Estadísticas de {ctx.author.name}",
    color=0x3498db
    )

    for tipo,cant in datos:

        embed.add_field(
        name=tipo,
        value=f"{cant} completados",
        inline=False
        )

    await ctx.send(embed=embed)

# ---------------- READY ----------------

@bot.event
async def on_ready():
    print("Bot conectado como",bot.user)
    revisar.start()
    actualizar_dashboard.start()

bot.run(TOKEN)
