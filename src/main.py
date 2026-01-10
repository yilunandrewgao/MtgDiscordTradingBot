import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os

from trade_manager import TradeManager
from config import MOXFIELD_REFRESH_HOURS, TRADER_ROLE, USERS_FILE
from trader import Trader
from moxfield.fetch_collections import fetch_all_collections

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

trade_manager = TradeManager()

bot = commands.Bot(command_prefix='!', intents=intents)

@tasks.loop(hours=MOXFIELD_REFRESH_HOURS)
async def update_collections():
    """Update all moxfield collections on an interval, skipping when bot starts"""
    if update_collections.current_loop != 0:
        try:
            fetch_all_collections()
            print("Successfully updated all collections")
        except Exception as e:
            print(f"Failed to update collections: {e}")

@bot.event
async def on_ready():
    
    print(f"We are ready to go, {bot.user.name}")

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server, {member.name}")

@bot.command()
async def link_moxfield(ctx):
    moxfield_id = ctx.message.content[ctx.message.content.find(' ') + 1:]
    discord_id = str(ctx.author.id)
    
    # Read users.json
    if discord_id not in trade_manager.traders:
        trade_manager.add_trader(
            discord_id=discord_id, 
            echomtg_token="", 
            moxfield_id=moxfield_id
        )
        
    else:
        trade_manager.get_trader(discord_id).moxfield_id = moxfield_id

    trade_manager.save_trader_info(discord_id)
    await ctx.send(f"{ctx.author.mention} has been added with moxfield collection!")

def filter_trades(available_trades, collection_number):
    # Filter trades to only include cards with matching collector number
        filtered_trades = {}
        for discord_id, cards in available_trades.items():
            matching_cards = {card_id: card for card_id, card in cards.items() if str(card.get('cn', '')) == collection_number}
            if matching_cards:
                filtered_trades[discord_id] = matching_cards
        return filtered_trades


def parse_search_input(message):
    """Parse the search input and return (card_name, collection_number|None).

    Raises ValueError with a user-facing message when the input is invalid.
    """
    start = message.find('{{')
    end = message.find('}}', start + 1)
    if start == -1 or end == -1 or start >= end:
        raise ValueError("Invalid format. Use !search {{card_name | collection_number}} or !search {{card_name}}")

    inner = message[start + 2:end]
    parts = inner.split('|', 1)
    card_name = parts[0].strip(' []{}')
    if len(card_name) < 5:
        raise ValueError("Please use a more specific query.")

    collection_number = parts[1].strip().lstrip('0') if len(parts) > 1 else None
    return card_name, collection_number

@bot.command()
async def search(ctx):
    try:
        card_name, collection_number = parse_search_input(ctx.message.content)
    except ValueError as e:
        await ctx.send(str(e))
        return

    discord_ids = [str(member.id) for member in ctx.guild.members if member.id != ctx.author.id]
    
    available_trades = trade_manager.search_for_card(card_name, discord_ids)

    if collection_number:
        available_trades = filter_trades(available_trades, collection_number)

    if not available_trades:
        await ctx.send("no cards found")
        return

    
    full_message = ""

    for discord_id in available_trades:
        discord_user = bot.get_user(int(discord_id))
        full_message += f"\n{discord_user.mention} has available trades: \n"
        cards = available_trades[discord_id]
        for card_id in cards:
            card = cards[card_id]
            full_message += f"{card['count']} copies of {{ {card['name']} \| #{card['cn']} \| {card['expansion']} }} .\n"
            found_results = True

    if len(full_message) > 2000:
        await ctx.send("Too many search results. Please use a more specific query.")
        return

    await ctx.send(full_message)

def parse_search_list_input(message):
    start = message.find('{{')
    end = message.find('}}', start + 1)
    if start == -1 or end == -1 or start >= end:
        raise ValueError("Invalid format. Use !search_list {{ card1 | card2 | card3 }}")

    inner = message[start + 2:end]
    parts = [p.strip(' []{}') for p in inner.split('|')]
    # Ignore purely-numeric tokens (collection numbers) and empty parts
    card_names = [p.strip() for p in parts]
    if not card_names:
        raise ValueError("No card names found. Use !search_list {{ card1 | card2 }}")
    return card_names


@bot.command()
async def search_list(ctx):
    try:
        card_names = parse_search_list_input(ctx.message.content)
    except ValueError as e:
        await ctx.send(str(e))
        return

    discord_ids = [str(member.id) for member in ctx.guild.members if member.id != ctx.author.id]

    # Aggregate results across all card names
    aggregated = {}
    for card_name in card_names:
        available_trades = trade_manager.search_for_card(card_name, discord_ids)
        for discord_id, cards in available_trades.items():
            if discord_id not in aggregated:
                aggregated[discord_id] = {}
            for card_id, card in cards.items():
                if card_id in aggregated[discord_id]:
                    aggregated[discord_id][card_id]['count'] = aggregated[discord_id][card_id].get('count', 0) + card.get('count', 0)
                else:
                    aggregated[discord_id][card_id] = card.copy()

    if not aggregated:
        await ctx.send("no cards found")
        return

    full_message = ""
    for discord_id in aggregated:
        discord_user = bot.get_user(int(discord_id))
        full_message += f"\n{discord_user.mention} has available trades: \n"
        cards = aggregated[discord_id]
        for card_id in cards:
            card = cards[card_id]
            full_message += f"{card.get('count', 0)} copies of {{ {card.get('name', '')} \| #{card.get('cn', '')} \| {card.get('expansion', '')} }} .\n"

    if len(full_message) > 2000:
        await ctx.send("Too many search results. Please use a more specific query.")
        return

    await ctx.send(full_message)

if __name__ == "__main__":
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)
