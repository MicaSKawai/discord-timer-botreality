import discord
from discord.ext import commands, tasks
import sqlite3
import time
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
CREATE TABLE IF NOT EXISTS timers(
user_id INTEGER,
username TEXT,
tipo TEXT,
fin INTEGER
)
""")

db.commit()


def ahora():
    return int(time.time())


async def iniciar_timer(ctx, tipo, horas):

    if ctx.channel.id != CANAL_REGISTRO:
        return

    fin = ahora() + horas * 3600

    cursor.execute(
        "INSERT INTO timers VALUES (?,?,?,?)",
        (ctx.author.id, ctx.author.name, tipo, fin)
    )
    db.commit()

    embed = discord.Embed(
        title="⏱️ Timer iniciado",
        description=f"{ctx.author.mention} inició **{tipo}**",
        color=0x00ffcc
    )

    embed.add_field(name="Duración", value=f"{horas} horas")

    await ctx.send(embed=embed)


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


@bot.command()
async def prueba(ctx):

    if ctx.channel.id != CANAL_REGISTRO:
        return

    fin = ahora() + 300

    cursor.execute(
        "INSERT INTO timers VALUES (?,?,?,?)",
        (ctx.author.id, ctx.author.name, "Prueba", fin)
    )
    db.commit()

    embed = discord.Embed(
        title="🧪 Timer de prueba",
        description=f"{ctx.author.mention} inició un timer de 5 minutos",
        color=0x00ffff
    )

    await ctx.send(embed=embed)


@bot.command()
async def timers(ctx):

    cursor.execute("SELECT * FROM timers")
    datos = cursor.fetchall()

    embed = discord.Embed(
        title="📊 Timers activos",
        color=0x3498db
    )

    for t in datos:

        restante = t[3] - ahora()

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
            msg = f"{user.mention} @everyone Ya puedes recoger tu cargamento de cajas!"
        elif tipo == "Capataz":
            msg = f"{user.mention} @everyone Ya está listo el capataz!"
        elif tipo == "Robo":
            msg = f"{user.mention} @everyone Ya puedes robar otra propiedad!"
        elif tipo == "Cargas":
            msg = f"{user.mention} VE A COMPRAR CARGADORES CON TODOS TUS PJs!"
        else:
            msg = f"{user.mention} @everyone Timer de prueba terminado!"

        embed = discord.Embed(
            title="✅ Timer terminado",
            description=msg,
            color=0x00ff00
        )

        await canal.send(embed=embed)

        cursor.execute(
            "DELETE FROM timers WHERE user_id=? AND tipo=? AND fin=?",
            (t[0], t[2], t[3])
        )

        db.commit()


@bot.event
async def on_ready():
    print("Bot conectado como", bot.user)
    revisar.start()


bot.run(TOKEN)
