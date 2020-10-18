"""
I had to open IE as admin, go to discord.com, click the lock to the
right of the url and issue a certificate to connect through SSL.
"""
import os

import discord
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')


client.run(TOKEN)
