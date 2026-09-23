import asyncio

import discord
from os import getenv
from dotenv import load_dotenv
from campaign import *

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

def load_campaign(guild_id):
    """Ingest the default books and build a character skeleton.

    Runs off the Discord event loop so gateway heartbeats can still be sent.

    Args:
        guild_id (int): Discord guild id used as the campaign data directory.

    Returns:
        None
    """
    campaign = Campaign(id=guild_id)
    campaign.add_lore("books/the_wild_sheep_chase_v2.pdf")
    campaign.add_rules("books/DnD_BasicRules_2018.pdf")
    campaign.add_rules("books/Monster Manual.pdf")
    campaign.gen_character_skeleton()
    return campaign


@client.event
async def on_guild_join(guild):
    await asyncio.to_thread(load_campaign, guild.id)
    print(f"Joined {guild.name}")
    channel = guild.text_channels[0]
    hook = Campaign(guild.id).query("Write a campaign hook to set the stage.")
    await channel.send(hook)


@client.event
async def on_message(message):
    if message.author == client.user or message.guild is None:
        return
    print("Message recieved! Reading chat log.")
    history = [msg async for msg in message.channel.history(limit=10)]
    history.reverse()
    transcript = "\n".join(
        f"{msg.author.display_name}: {msg.content}" for msg in history
    )
    print("Chat log read. Forming response.")
    campaign = Campaign(message.guild.id)
    response = await asyncio.to_thread(campaign.query, "Continue the scene as the dungeon master.\n\n" + transcript)
    print("Response finished.")
    await message.channel.send(response)

load_dotenv()
bot_token = getenv("DISCORD_BOT_TOKEN")
print(bot_token)
client.run(bot_token)