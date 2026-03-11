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

db.commit()

# ---------------- TIEMPO ----------------

def ahora():
    return int(time.time())

def hora_local(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M")

def hora_hub(ts):
    return (datetime.fromtimestamp(ts) + timedelta(hours=3)).strftime("%H:%M")

def tiempo_restante(seg):

    horas = seg // 3600
    minutos = (seg % 3600) // 60

    if horas > 0:
        return f"{horas}h {minutos}m"
    else:
        return f"{minutos}m"

# ---------------- TIMER ----------------

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

    if horas < 1:
        duracion = f"{int(horas*60)} minutos"
    else:
        duracion = f"{horas} horas"

    embed = discord.Embed(
        title="⏱ Timer iniciado",
        color=0x00ffaa
    )

    embed.add_field(name="Usuario", value=ctx.author.mention, inline=False)
    embed.add_field(name="Acción", value=tipo, inline=True)
    embed.add_field(name="Duración", value=duracion, inline=True)

    embed.add_field(name="Inicio Local", value=hora_local(inicio))
    embed.add_field(name="Inicio HUB", value=hora_hub(inicio))

    embed.add_field(name="Fin Local", value=hora_local(fin))
    embed.add_field(name="Fin HUB", value=hora_hub(fin))

    await ctx.send(embed=embed)

# ---------------- COMANDOS ----------------

@bot.command()
async def cajas(ctx):
    await iniciar_timer(ctx,"Cajas",3)

@bot.command()
async def capataz(ctx):
    await iniciar_timer(ctx,"Capataz",5)

@bot.command()
async def robo(ctx):
    await iniciar_timer(ctx,"Robo",2)

@bot.command()
async def cargas(ctx):
    await iniciar_timer(ctx,"Cargas",72)

@bot.command()
async def test(ctx):
    await iniciar_timer(ctx,"Test",0.0167)

# ---------------- PANEL ----------------

class Panel(discord.ui.View):

    @discord.ui.button(label="📦 Cajas",style=discord.ButtonStyle.primary)
    async def cajas(self,interaction:discord.Interaction,button:discord.ui.Button):

        inicio = ahora()
        fin = inicio + 3*3600

        cursor.execute("INSERT INTO timers VALUES (?,?,?,?,?)",
        (interaction.user.id,interaction.user.name,"Cajas",inicio,fin))
        db.commit()

        await interaction.response.send_message("📦 Timer de cajas iniciado",ephemeral=True)

    @discord.ui.button(label="💰 Robo",style=discord.ButtonStyle.danger)
    async def robo(self,interaction:discord.Interaction,button:discord.ui.Button):

        inicio = ahora()
        fin = inicio + 2*3600

        cursor.execute("INSERT INTO timers VALUES (?,?,?,?,?)",
        (interaction.user.id,interaction.user.name,"Robo",inicio,fin))
        db.commit()

        await interaction.response.send_message("💰 Timer de robo iniciado",ephemeral=True)

    @discord.ui.button(label="👷 Capataz",style=discord.ButtonStyle.success)
    async def capataz(self,interaction:discord.Interaction,button:discord.ui.Button):

        inicio = ahora()
        fin = inicio + 5*3600

        cursor.execute("INSERT INTO timers VALUES (?,?,?,?,?)",
        (interaction.user.id,interaction.user.name,"Capataz",inicio,fin))
        db.commit()

        await interaction.response.send_message("👷 Timer capataz iniciado",ephemeral=True)

    @discord.ui.button(label="🔫 Cargas",style=discord.ButtonStyle.secondary)
    async def cargas(self,interaction:discord.Interaction,button:discord.ui.Button):

        inicio = ahora()
        fin = inicio + 72*3600

        cursor.execute("INSERT INTO timers VALUES (?,?,?,?,?)",
        (interaction.user.id,interaction.user.name,"Cargas",inicio,fin))
        db.commit()

        await interaction.response.send_message("🔫 Timer de cargas iniciado",ephemeral=True)

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

dashboard_message = None

@bot.command()
async def dashboard(ctx):

    global dashboard_message

    if ctx.channel.id != CANAL_DASHBOARD:
        return

    embed = discord.Embed(
        title="📊 Timers Activos del Servidor",
        description="Panel automático",
        color=0x2ecc71
    )

    dashboard_message = await ctx.send(embed=embed)

@tasks.loop(seconds=30)
async def actualizar_dashboard():

    global dashboard_message

    if dashboard_message is None:
        return

    cursor.execute("SELECT * FROM timers")
    datos = cursor.fetchall()

    embed = discord.Embed(
        title="📊 Timers Activos del Servidor",
        color=0x2ecc71
    )

    if not datos:
        embed.add_field(
            name="Sin timers",
            value="Nadie tiene timers activos",
            inline=False
        )

    for t in datos:

        restante = t[4] - ahora()

        if restante <= 0:
            continue

        embed.add_field(
            name=f"{t[2]} • {t[1]}",
            value=f"⏳ {tiempo_restante(restante)} restantes",
            inline=False
        )

    try:
        await dashboard_message.edit(embed=embed)
    except:
        pass

# ---------------- REVISION TIMERS ----------------

@tasks.loop(seconds=30)
async def revisar():

    cursor.execute("SELECT * FROM timers WHERE fin <= ?",(ahora(),))
    lista = cursor.fetchall()

    if not lista:
        return

    canal = bot.get_channel(CANAL_AVISOS)

    for t in lista:

        user = await bot.fetch_user(t[0])
        tipo = t[2]

        embed = discord.Embed(
            title="✅ Timer finalizado",
            description=f"{user.mention} Tu timer **{tipo}** terminó.",
            color=0x00ff00
        )

        await canal.send(embed=embed)

        cursor.execute(
            "DELETE FROM timers WHERE user_id=? AND tipo=? AND inicio=? AND fin=?",
            (t[0],t[2],t[3],t[4])
        )

        db.commit()

# ---------------- READY ----------------

@bot.event
async def on_ready():
    print("Bot conectado como",bot.user)
    revisar.start()
    actualizar_dashboard.start()

bot.run(TOKEN)
