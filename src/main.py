from curl_cffi.requests import AsyncSession
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import re
import parsy

from trade_manager import TradeManager
from config import MOXFIELD_REFRESH_HOURS, TRADER_ROLE, USERS_FILE
from trader import AvailableTrades, MoxfieldType, call_moxfield_api
from decklist_parser import parse_decklist

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
assert token is not None, "DISCORD_TOKEN environment variable is not set"

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

trade_manager = TradeManager()

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    
    assert bot.user is not None
    print(f"We are ready to go, {bot.user.name}")

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server, {member.name}")

async def extract_moxfield_info(ctx: commands.Context) -> tuple[str, MoxfieldType] | None:
    content = ctx.message.content
    headers = {"User-Agent": "MtgDiscordTrading"}

    async with AsyncSession(impersonate="chrome", headers=headers) as session:
        binder_match = re.search(r'binders?/([A-Za-z0-9_-]+)', content)
        if binder_match:
            binder_id = binder_match.group(1)
            try:
                response = await call_moxfield_api(session, moxfield_id=binder_id, moxfield_type="binder")
            except Exception:
                return None
            if response and response.get('tradeBinder'):
                return binder_id, "binder"
            return None

        collection_match = re.search(r'(?:collection/)?([A-Za-z0-9_-]+)\/?$', content)
        if collection_match:
            collection_id = collection_match.group(1)
            try:
                response = await call_moxfield_api(session, moxfield_id=collection_id)
            except Exception:
                return None
            if response and response.get('data'):
                return collection_id, "collection"
            return None

    return None

@bot.command()
async def link_moxfield(ctx):
    result = await extract_moxfield_info(ctx)
    if not result:
        await ctx.send(f"Invalid moxfield collection or binder link or ID.")
        return

    moxfield_id, moxfield_type = result
    discord_id = str(ctx.author.id)

    if discord_id not in trade_manager.traders:
        trade_manager.add_trader(
            discord_id=discord_id,
            moxfield_id=moxfield_id,
            moxfield_type=moxfield_type
        )
    else:
        trader = trade_manager.get_trader(discord_id)
        trader.moxfield_id = moxfield_id
        trader.moxfield_type = moxfield_type

    trade_manager.save_trader_info(discord_id)
    await ctx.send(f"{ctx.author.mention} has been added with moxfield {moxfield_type} id: {moxfield_id}")

@bot.command()
async def unlink_moxfield(ctx):
    discord_id = str(ctx.author.id)
    removed = trade_manager.remove_trader(discord_id)
    if removed:
        await ctx.send(f"{ctx.author.mention} has been unlinked from their moxfield collection.")
    else:
        await ctx.send(f"{ctx.author.mention} has no linked moxfield collection.")

def filter_trades(available_trades: AvailableTrades, collection_number: str) -> AvailableTrades:
    # Filter trades to only include cards with matching collector number
        filtered_trades = {}
        for discord_id, cards in available_trades.items():
            matching_cards = {card_id: card for card_id, card in cards.items() if str(card.get('cn', '')) == collection_number}
            if matching_cards:
                filtered_trades[discord_id] = matching_cards
        return filtered_trades


def parse_search_input(content: str) -> tuple[str, str | None]:
    """Parse the search input and return (card_name, collection_number|None).

    Raises ValueError with a user-facing message when the input is invalid.
    """
    try:
        cards = parse_decklist(content)
        if len(cards) == 1:
            card = cards[0]
            cn = card.collector_number.lstrip('0') if card.collector_number else None
            return card.name, cn
        elif len(cards) > 1:
            raise ValueError("!search only supports a single card. Use !search_list for multiple cards.")
    except parsy.ParseError:
        logging.debug("Decklist parse failed, falling back to legacy format", exc_info=True)

    start = content.find('{{')
    end = content.find('}}', start + 1)
    if start == -1 or end == -1 or start >= end:
        raise ValueError("Invalid format. Paste a Moxfield export line (e.g. `1 Counterspell (CMR) 632`), or use `!search {{card_name | collector_number}}`.")

    inner = content[start + 2:end]
    parts = inner.split('|', 1)
    card_name = parts[0].strip(' []{}')
    if len(card_name) < 5:
        raise ValueError("Please use a more specific query.")

    collection_number = parts[1].strip().lstrip('0') if len(parts) > 1 else None
    return card_name, collection_number

def generate_messages_from_lines(lines: list[str], max_message_length: int = 2000) -> list[str]:

    messages = []
    current_message = ""
    for line in lines:
        if len(current_message) + len(line) > max_message_length:
            messages.append(current_message)
            current_message = ""
        current_message += line

    if current_message:
        messages.append(current_message)

    return messages


def generate_message_from_trades(available_trades: AvailableTrades, max_message_length: int = 2000) -> list[str]:

    if not available_trades:
        return ["no cards found"]

    lines = []

    for discord_id in available_trades:
        discord_user = bot.get_user(int(discord_id))
        if discord_user is None:
            continue
        lines.append(f"{discord_user.mention} has available trades: \n")
        cards = available_trades[discord_id]
        for card_id in cards:
            card = cards[card_id]
            lines.append(f"{card['count']} copies of {{ {card['name']} \\| #{card['cn']} \\| {card['expansion']} }} .\n")


    return generate_messages_from_lines(lines, max_message_length)

@bot.command()
async def search(ctx, *, content=''):
    try:
        card_name, collection_number = parse_search_input(content)
    except ValueError as e:
        await ctx.send(str(e))
        return

    discord_ids = {str(member.id) for member in ctx.guild.members if member.id != ctx.author.id}

    available_trades = await trade_manager.search_for_card(card_name, discord_ids)

    if collection_number:
        available_trades = filter_trades(available_trades, collection_number)

    for message in generate_message_from_trades(available_trades):
        await ctx.send(message)

def parse_search_list_input(content: str) -> list[str]:
    try:
        cards = parse_decklist(content)
        if cards:
            return [card.name for card in cards]
    except Exception:
        logging.debug("Decklist parse failed, falling back to legacy format", exc_info=True)

    start = content.find('{{')
    end = content.find('}}', start + 1)
    if start == -1 or end == -1 or start >= end:
        raise ValueError("Invalid format. Paste a Moxfield export (one card per line), or use `!search_list {{ card1 | card2 }}`.")

    inner = content[start + 2:end]
    parts = [p.strip(' []{}') for p in inner.split('|')]
    # Ignore purely-numeric tokens (collection numbers) and empty parts
    card_names = [p.strip() for p in parts]
    if not card_names:
        raise ValueError("No card names found. Use !search_list {{ card1 | card2 }}")
    return card_names


@bot.command()
async def search_list(ctx, *, content=''):
    try:
        card_names = parse_search_list_input(content)
    except ValueError as e:
        await ctx.send(str(e))
        return

    discord_ids = {str(member.id) for member in ctx.guild.members if member.id != ctx.author.id}

    available_trades = await trade_manager.search_for_card(' or '.join([f'{name}' for name in card_names]), discord_ids)

    for message in generate_message_from_trades(available_trades):
        await ctx.send(message)

@bot.command()
async def search_self(ctx, *, content=''):
    try:
        card_names = parse_search_list_input(content)
    except ValueError as e:
        await ctx.send(str(e))
        return

    discord_ids = {str(ctx.author.id)}

    available_trades = await trade_manager.search_for_card(' or '.join([f'{name}' for name in card_names]), discord_ids)

    for message in generate_message_from_trades(available_trades):
        await ctx.send(message)

if __name__ == "__main__":
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)
