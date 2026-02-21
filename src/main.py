import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import re

from trade_manager import TradeManager
from config import MOXFIELD_REFRESH_HOURS, TRADER_ROLE, USERS_FILE
from moxfield_api import call_moxfield_collection_api, call_moxfield_deck_api

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

trade_manager = TradeManager()

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    
    print(f"We are ready to go, {bot.user.name}")

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server, {member.name}")

def extract_moxfield_id(ctx):
    pattern = r'(?:collection/)?([A-Za-z0-9_-]+)\/?$'
    
    match = re.search(pattern, ctx.message.content)
    if match:
        collection_id = match.group(1)
        # Validate collection_id
        try:
            response = call_moxfield_collection_api(moxfield_id=collection_id)
        except Exception:
            return None
        # If we get a valid response with data, the collection is valid
        if response and response.get('data'):
            return collection_id
        else:
            return None

    return None

def extract_deck_id(ctx):
    pattern = r'(?:decks/)?([A-Za-z0-9_-]+)\/?$'

    match = re.search(pattern, ctx.message.content)
    if match:
        deck_id = match.group(1)
        try:
            response = call_moxfield_deck_api(deck_id=deck_id)
        except Exception:
            return None
        if response:
            return deck_id
        else:
            return None

    return None

@bot.command()
async def link_moxfield(ctx):
    moxfield_id = extract_moxfield_id(ctx)
    if not moxfield_id:
        await ctx.send(f"Invalid moxfield collection link or ID.")
        return
    
    discord_id = str(ctx.author.id)
    
    # Read users.json
    if discord_id not in trade_manager.traders:
        trade_manager.add_trader(
            discord_id=discord_id,
            moxfield_id=moxfield_id
        )
        
    else:
        trade_manager.get_trader(discord_id).moxfield_id = moxfield_id

    trade_manager.save_trader_info(discord_id)
    await ctx.send(f"{ctx.author.mention} has been added with moxfield collection id: {moxfield_id}")

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


def generate_message_from_trades(available_trades):
    messages = []
    current_message = ""

    for discord_id in available_trades:
        discord_user = bot.get_user(int(discord_id))
        user_header = f"\n{discord_user.mention} has available trades: \n"
        cards = available_trades[discord_id]
        
        # Check if adding user header would exceed limit
        if current_message and len(current_message) + len(user_header) > 2000:
            messages.append(current_message)
            current_message = user_header
        else:
            current_message += user_header
        
        # Add each card
        for card_id in cards:
            card = cards[card_id]
            card_line = f"{card['count']} copies of {{ {card['name']} \| #{card['cn']} \| {card['expansion']} }} .\n"
            
            if len(current_message) + len(card_line) > 2000:
                messages.append(current_message)
                current_message = card_line
            else:
                current_message += card_line
    
    if current_message:
        messages.append(current_message)
    
    return messages


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

    messages = generate_message_from_trades(available_trades)
    for message in messages:
        await ctx.send(message)

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

    available_trades = trade_manager.search_for_card(' or '.join([f'{name}' for name in card_names]), discord_ids)

    messages = generate_message_from_trades(available_trades)
    for message in messages:
        await ctx.send(message)

@bot.command()
async def search_self(ctx):
    try:
        card_names = parse_search_list_input(ctx.message.content)
    except ValueError as e:
        await ctx.send(str(e))
        return

    discord_ids = [str(ctx.author.id)]

    available_trades = trade_manager.search_for_card(' or '.join([f'{name}' for name in card_names]), discord_ids)

    messages = generate_message_from_trades(available_trades)
    for message in messages:
        await ctx.send(message)

@bot.command()
async def search_deck(ctx):
    deck_id = extract_deck_id(ctx)
    if not deck_id:
        await ctx.send(f"Invalid moxfield deck link or ID.")
        return
    
    response = call_moxfield_deck_api(deck_id=deck_id)
    if response:
        cards_in_main_and_side = response.get('boards').get('mainboard').get('cards') | \
            response.get('boards').get('sideboard').get('cards')    
        
        unique_cards = set()
        for entry in cards_in_main_and_side.values():
            card_name = entry.get('card').get('name')
            unique_cards.add(card_name)

        unique_cards = unique_cards.difference({'Plains', 'Island', 'Swamp', 'Mountain', 'Forest'})

    discord_ids = [str(member.id) for member in ctx.guild.members if member.id != ctx.author.id]

    available_trades = trade_manager.search_for_card(' or '.join([f'{name}' for name in unique_cards]), discord_ids)

    messages = generate_message_from_trades(available_trades)
    for message in messages:
        await ctx.send(message)

if __name__ == "__main__":
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)

        