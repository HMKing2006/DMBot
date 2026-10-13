import asyncio
import functools
import json
from pathlib import Path

import discord
from os import getenv
from dotenv import load_dotenv
from campaign import Campaign


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

CREATION_PROMPT = (
    "You are the dungeon master, helping player {player_id} create a character over DM. "
    "If the conversation is empty, open with a short thematic introduction to the campaign. "
    "Ask one simple question at a time. Use your tools to roll dice when the rules call for it "
    "and save every answer to the sheet as you go. When the sheet is complete, show the player "
    "a summary and ask them to confirm; call finish_character only after they confirm.\n\n"
    "Sheet: {sheet}\n\nConversation:\n{transcript}"
)


@functools.cache
def get_campaign(guild_id):
    return Campaign(guild_id)


def default_channel(guild):
    return guild.system_channel or next(
        (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None
    )


async def transcript(channel, limit, keep=lambda _: True):
    msgs = [msg async for msg in channel.history(limit=limit) if keep(msg)]
    return "\n".join(f"{m.author.display_name} ({m.author.id}): {m.content}" for m in reversed(msgs))


async def creation_turn(campaign, user, dm_channel):
    """Run one character-creation exchange; announce the character once finished."""
    prompt = CREATION_PROMPT.format(
        player_id=user.id, sheet=json.dumps(campaign.sheet(user.id)), transcript=await transcript(dm_channel, 20)
    )
    tools = {**campaign.tools, "finish_character": (
        lambda: campaign.finish_character(user.id), "Mark the character finished once the player confirms.", {},
    )}
    if reply := await asyncio.to_thread(campaign.query, prompt, tools=tools):
        await dm_channel.send(reply)
    if str(user.id) in campaign.get_players() and (channel := default_channel(client.get_guild(campaign.id))):
        intro = await asyncio.to_thread(
            campaign.query, f"Introduce this new character to the party in a few sentences: {campaign.sheet(user.id)}"
        )
        await channel.send(f"{user.mention} joins the party!\n{intro}")


def load_campaign(guild_id):
    """Ingest the default books and build a character skeleton."""
    campaign = get_campaign(guild_id)
    campaign.add_lore("books/the_wild_sheep_chase_v2.pdf")
    campaign.add_rules("books/DnD_BasicRules_2018.pdf")
    campaign.add_rules("books/Monster Manual.pdf")
    campaign.gen_character_skeleton()
    return campaign


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_guild_join(guild):
    campaign = await asyncio.to_thread(load_campaign, guild.id)
    print(f"Joined {guild.name}")
    if channel := default_channel(guild):
        await channel.send(await asyncio.to_thread(campaign.query, "Write a campaign hook to set the stage."))


@client.event
async def on_message(message):
    if message.author.bot:
        return
    drafts = list(Path("data").glob(f"*/drafts/{message.author.id}.json"))

    if message.guild is None:
        if not drafts:
            await message.channel.send("You're not creating a character. Say something in a campaign server to start.")
            return
        await creation_turn(get_campaign(int(drafts[0].parts[1])), message.author, message.channel)
        return

    campaign = get_campaign(message.guild.id)
    players = campaign.get_players()
    if str(message.author.id) in players:
        log = await transcript(message.channel, 10, lambda m: str(m.author.id) in players or m.author == client.user)
        prompt = (
            "Continue the scene as the dungeon master. Use your tools to roll dice and keep sheets current.\n\n"
            f"Player sheets: {json.dumps({p: campaign.sheet(p) for p in players})}\n\n{log}"
        )
        if reply := await asyncio.to_thread(campaign.query, prompt, tools=campaign.tools):
            await message.channel.send(reply)
    elif not drafts:
        campaign.start_character(message.author.id)
        try:
            await creation_turn(campaign, message.author, await message.author.create_dm())
        except discord.Forbidden:
            campaign.sheet_path(message.author.id).unlink()
            await message.channel.send(
                f"{message.author.mention} I couldn't DM you. Please allow DMs from server members."
            )


load_dotenv()
client.run(getenv("DISCORD_BOT_TOKEN"))
