import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import sqlite3
from sqlite3 import Error
import datetime
import asyncio
from prometheus_client import start_http_server, Counter, Gauge
import random
import time


print("Demarrage du bot...")
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True

# Ouvrir le fichier "script.py"
with open('db_setup.py', 'r') as f:
    exec(f.read(), globals(), locals())

bot = commands.Bot(command_prefix="!", intents=intents)
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "db", "petitions.db")


# ------Ajout de la bibliothèque prometheus_client------ #
# compteurs pour les métriques
messages_received = Counter("bot_messages_received_total", "Nombre de messages reçus par le bot")
commands_executed = Counter("bot_commands_executed_total", "Nombre de commandes exécutées par le bot")
bot_latency = Gauge("bot_latency_seconds", "Latence du bot en secondes")

# serveur HTTP pour exposer les metriques
start_http_server(8000)

# mettre à jour les compteurs dans vos fonctions de gestion des événements et commandes
@bot.event
async def on_message(message):
    start_time = time.time()
    messages_received.inc()
    await bot.process_commands(message)
    latency = time.time() - start_time
    bot_latency.set(latency)

@bot.command(name="example_command")
async def _example_command(ctx):
    commands_executed.inc()
    await ctx.send("Commande exemple exécutée")

async def create_petition(ctx, title: str, content: str, duration: int):
    print("Création de la pétition :", title, content, duration)
    print("Chemin de la base de données:", db_path)
    print(title, content, duration)
    try:
        conn = sqlite3.connect("./db/petitions.db")
        cursor = conn.cursor()
        created_at = datetime.datetime.now()
        cursor.execute("INSERT INTO petitions (title, content, duration, created_at) VALUES (?, ?, ?, ?)", (title, content, duration, created_at))
        conn.commit()
        petition_id = cursor.lastrowid
        conn.close()

        embed = discord.Embed(title=title, description=content, color=0x00ff00)
        embed.set_footer(text=f"ID de la pétition: {petition_id}")
        await ctx.send(embed=embed)

        # Ajout d'un timer asynchrone
        await asyncio.sleep(duration)

        # Fermeture de la pétition après la durée spécifiée
        conn = sqlite3.connect("./db/petitions.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE petitions SET status = 'closed' WHERE id = ?", (petition_id,))
        conn.commit()
        conn.close()

        await ctx.send(f"La pétition {petition_id} est maintenant fermée.")

    except Error as e:
        await ctx.send(e)
        await ctx.send("Erreur lors de la création de la pétition")


@bot.command(name="create_petition")
async def _create_petition(ctx, *, args):
    title, content, duration = args.split('|')
    await create_petition(ctx, title.strip(), content.strip(), int(duration.strip()))

# @bot.command(name="create_petition")
# async def _create_petition(ctx, title: str, content: str, duration: int):
#     await create_petition(ctx, title, content, duration)


@bot.event
async def on_ready():
    print(f'{bot.user.name} est connecté à Discord!')
    update_petitions_status.start()
    
async def vote_petition(ctx, petition_id: int, vote: str):
    user_id = ctx.author.id
    try:
        conn = sqlite3.connect("./db/petitions.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM petitions WHERE id=? AND status='open'", (petition_id,))
        petition = cursor.fetchone()

        if petition:
            cursor.execute("SELECT * FROM votes WHERE user_id=? AND petition_id=?", (user_id, petition_id))
            user_vote = cursor.fetchone()

            if user_vote:
                await ctx.send("Vous avez déjà voté pour cette pétition.")
                return

            if vote.lower() == "oui":
                cursor.execute("UPDATE petitions SET yes_votes = yes_votes + 1 WHERE id=?", (petition_id,))
                cursor.execute("INSERT INTO votes (user_id, petition_id, vote) VALUES (?, ?, ?)", (user_id, petition_id, vote))
            elif vote.lower() == "non":
                cursor.execute("UPDATE petitions SET no_votes = no_votes + 1 WHERE id=?", (petition_id,))
                cursor.execute("INSERT INTO votes (user_id, petition_id, vote) VALUES (?, ?, ?)", (user_id, petition_id, vote))
            else:
                await ctx.send("Vote non valide. Utilisez 'oui' ou 'non'")
                return

            conn.commit()
            await ctx.send("Votre vote a été enregistré.")
        else:
            await ctx.send("Pétition introuvable")

        conn.close()
    except Error as e:
        print(e)
        print(f"Erreur lors du vote: {e}")
        await ctx.send("Erreur lors du vote")

'''
async def vote_petition(ctx, petition_id: int, vote: str):
    try:
        conn = sqlite3.connect("./db/petitions.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM petitions WHERE id=? AND status='open'", (petition_id,))
        petition = cursor.fetchone()

        if petition:
            if vote.lower() == "oui":
                cursor.execute("UPDATE petitions SET yes_votes = yes_votes + 1 WHERE id=?", (petition_id,))
            elif vote.lower() == "non":
                cursor.execute("UPDATE petitions SET no_votes = no_votes + 1 WHERE id=?", (petition_id,))
            else:
                await ctx.send("Vote non valide. Utilisez 'oui' ou 'non'")
                return

            conn.commit()
            await ctx.send("Votre vote a été enregistré.")
        else:
            await ctx.send("Pétition introuvable")

        conn.close()
    except Error as e:
        print(e)
        await ctx.send("Erreur lors du vote")
'''


@bot.command(name="vote")
async def _vote(ctx, petition_id: int, vote: str):
    await vote_petition(ctx, petition_id, vote)


async def check_petitions_status():
    now = datetime.datetime.now()
    conn = sqlite3.connect("./db/petitions.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM petitions WHERE status='open'")
    petitions = cursor.fetchall()

    for petition in petitions:
        id, title, content, duration, status, yes_votes, no_votes, created_at = petition
        petition_end_time = datetime.datetime.fromtimestamp(id) + datetime.timedelta(seconds=duration)

        if now >= petition_end_time:
            if yes_votes > no_votes:
                status = 'accepted'
            else:
                status = 'rejected'

            cursor.execute("UPDATE petitions SET status=? WHERE id=?", (status, id))
            conn.commit()

    conn.close()

@tasks.loop(seconds=60)
async def update_petitions_status():
    await check_petitions_status()

bot.run(TOKEN)
