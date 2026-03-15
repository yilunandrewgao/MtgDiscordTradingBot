import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import re

from models.moxfield_types import MoxfieldAsset
from trade_manager import TradeManager, TraderNotFound
from trader import AvailableTrades
from moxfield_api import call_moxfield_api_sync, get_decklist_export
from decklist_parser import CardQuery, parse_decklist

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
assert token is not None, "DISCORD_TOKEN environment variable is not set"

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

trade_manager = TradeManager()

bot = commands.Bot(command_prefix='!', intents=intents)

logger = logging.getLogger(__name__)

@bot.event
async def on_ready():
    
    assert bot.user is not None
    print(f"We are ready to go, {bot.user.name}")

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server, {member.name}")

def extract_moxfield_info(
        ctx: commands.Context,
        moxfield_type: MoxfieldAsset = MoxfieldAsset.COLLECTION
    ) -> tuple[str, MoxfieldAsset]:

    content = ctx.message.content

    regexes = {
        MoxfieldAsset.BINDER: r'binders?/([A-Za-z0-9_-]+)\/?$',
        MoxfieldAsset.DECK: r'decks?/([A-Za-z0-9_-]+)\/?$',
        MoxfieldAsset.COLLECTION: r'collection?/([A-Za-z0-9_-]+)\/?$'
    }

    match = re.search(regexes[moxfield_type], content)
    if match:
        id = match.group(1)
        try:
            response = call_moxfield_api_sync(moxfield_id=id, moxfield_type=moxfield_type)
        except Exception as e:
            logger.exception(f"Error calling moxfield API: {e}")
            raise ValueError(f"Invalid moxfield {moxfield_type.value} ID: {id}")
        if response:
            return id, moxfield_type
    raise ValueError(f"Could not extract moxfield {moxfield_type.value} ID from message")


async def _link_moxfield(ctx, moxfield_type: MoxfieldAsset = MoxfieldAsset.COLLECTION):
    try:
        moxfield_id, moxfield_type = extract_moxfield_info(ctx, moxfield_type)
    except ValueError as e:
        await ctx.send(str(e))
        return

    discord_id = str(ctx.author.id)
    trade_manager.upsert_trader(discord_id, moxfield_id, moxfield_type)
    await ctx.send(f"{ctx.author.mention} has been added with moxfield {moxfield_type.value} id: {moxfield_id}")

@bot.command()
async def link_moxfield(ctx):

    if MoxfieldAsset.BINDER.value in ctx.message.content:
        await _link_moxfield(ctx, MoxfieldAsset.BINDER)
    else:
        await _link_moxfield(ctx, MoxfieldAsset.COLLECTION)

@bot.command()
async def unlink_moxfield(ctx):
    discord_id = str(ctx.author.id)
    removed = trade_manager.remove_trader(discord_id)
    if removed:
        await ctx.send(f"{ctx.author.mention} has been unlinked from their moxfield collection.")
    else:
        await ctx.send(f"{ctx.author.mention} has no linked moxfield collection.")

@bot.command()
async def link_wishlist(ctx: commands.Context):
    discord_id = str(ctx.author.id)

    try:
        wishlist_id, _ = extract_moxfield_info(ctx, MoxfieldAsset.DECK)
        trader = trade_manager.set_wishlist(discord_id, wishlist_id)
    except ValueError as e:
        await ctx.send(str(e))
        return
    except TraderNotFound:
        await ctx.send(f"{ctx.author.mention} must link a Moxfield collection first with !link_moxfield.")
        return
    await ctx.send(f"{ctx.author.mention} wishlist linked: {trader.wishlist_url}")

@bot.command()
async def unlink_wishlist(ctx: commands.Context):
    discord_id = str(ctx.author.id)

    try:
        removed = trade_manager.remove_wishlist(discord_id)
    except TraderNotFound:
        await ctx.send(f"{ctx.author.mention} must link a Moxfield collection first with !link_moxfield.")
        return
    if removed:
        await ctx.send(f"{ctx.author.mention} wishlist has been unlinked.")
    else:
        await ctx.send(f"{ctx.author.mention} has no linked wishlist.")

def parse_search_input(content: str) -> list[CardQuery]:
    """Parse search input into a list of cards. Raises ValueError when the input is invalid."""
    cards = parse_decklist(content)
    if cards:
        return cards
    raise ValueError("Invalid format. Paste a Moxfield export (e.g. `1 Counterspell (CMR) 632`).")

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
        trader = trade_manager.get_trader(discord_id)
        wishlist_url = trader.wishlist_url if trader else None
        if wishlist_url:
            lines.append(f"{discord_user.mention} ([WL]({wishlist_url})) has available trades: \n")
        else:
            lines.append(f"{discord_user.mention} has available trades: \n")
        cards = available_trades[discord_id]
        for card_id in cards:
            card = cards[card_id]
            lines.append(f"{card['count']} copies of {{ {card['name']} \\| #{card['cn']} \\| {card['expansion']} }} .\n")


    return generate_messages_from_lines(lines, max_message_length)

async def _search_impl(ctx, *, content=''):
    try:
        cards = parse_search_input(content)
    except ValueError as e:
        await ctx.send(str(e))
        return

    discord_ids = {str(member.id) for member in ctx.guild.members if member.id != ctx.author.id}
    available_trades = await trade_manager.fuzzy_search(cards, discord_ids)

    for message in generate_message_from_trades(available_trades):
        await ctx.send(message)

async def _search_exact_impl(ctx, *, content=''):
    try:
        cards = parse_search_input(content)
    except ValueError as e:
        await ctx.send(str(e))
        return

    discord_ids = {str(member.id) for member in ctx.guild.members if member.id != ctx.author.id}
    available_trades = await trade_manager.exact_search(cards, discord_ids)

    for message in generate_message_from_trades(available_trades):
        await ctx.send(message)

@bot.command()
async def search(ctx, *, content=''):
    await _search_impl(ctx=ctx, content=content)

@bot.command()
async def search_exact(ctx, *, content=''):
    await _search_exact_impl(ctx=ctx, content=content)

@bot.command()
async def search_deck(ctx):
    deck_id, _ = extract_moxfield_info(ctx, MoxfieldAsset.DECK)
    exported_cards = get_decklist_export(deck_id)
    await _search_impl(ctx=ctx, content=exported_cards)

@bot.command()
async def search_deck_exact(ctx):
    deck_id, _ = extract_moxfield_info(ctx, MoxfieldAsset.DECK)
    exported_cards = get_decklist_export(deck_id)
    await _search_exact_impl(ctx=ctx, content=exported_cards)

@bot.command()
async def search_self(ctx, *, content=''):
    try:
        cards = parse_search_input(content)
    except ValueError as e:
        await ctx.send(str(e))
        return

    discord_ids = {str(ctx.author.id)}

    query = ' or '.join(card.name for card in cards)
    available_trades = await trade_manager.search_for_card(query, discord_ids)

    for message in generate_message_from_trades(available_trades):
        await ctx.send(message)

if __name__ == "__main__":
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)
