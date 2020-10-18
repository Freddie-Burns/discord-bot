"""
I had to open IE as admin, go to discord.com, click the lock to the
right of the url and issue a certificate to connect through SSL.
"""
import os

import discord
from dotenv import load_dotenv


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

client = discord.Client()


@client.event
async def on_ready():
    guild = discord.utils.get(client.guilds, name=GUILD)
    print(f'{client.user} has connected to the guild:\n'
          f'{guild.name}(id: {guild.id})')


class CustomClient(discord.Client):
    async def on_ready(self):
        print(f'{client.user} has connected!')


# client.run(TOKEN)
custom_client = CustomClient()
custom_client.run(TOKEN)
