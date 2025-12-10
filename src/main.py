import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import json

from trade_manager import TradeManager
from config import TRADER_ROLE, USERS_FILE
from trader import Trader

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

    ## Create MtgTrader role if it does not already exist
    for guild in bot.guilds:
        if TRADER_ROLE not in [role.name for role in guild.roles]:
            await guild.create_role(name=TRADER_ROLE)
    
    print(f"We are ready to go, {bot.user.name}")

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server, {member.name}")

@bot.command()
async def start_trading(ctx):
    role = discord.utils.get(ctx.guild.roles, name=TRADER_ROLE)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} is now assigned to {TRADER_ROLE}")
    else:
        await ctx.send(f"role does not exist")

@bot.command()
async def stop_trading(ctx):
    role = discord.utils.get(ctx.guild.roles, name=TRADER_ROLE)
    if role:
        await ctx.author.remove_roles(role)
        await ctx.send(f"{ctx.author.mention} is now unassigned to {TRADER_ROLE}")
    else:
        await ctx.send(f"role does not exist")

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

@bot.command()
async def search(ctx):
    active_discord_ids = [str(member.id) for member in ctx.guild.members if TRADER_ROLE in [role.name for role in member.roles]]
    card_name = ctx.message.content[ctx.message.content.find(' ') + 1:]
    available_trades = trade_manager.search_for_card(card_name, active_discord_ids)

    if not available_trades:
        await ctx.send("no cards found")
        return

    full_message = ""

    for discord_id in available_trades:
        discord_user = bot.get_user(int(discord_id))
        full_message += f"\n{discord_user.mention} has available trades: \n"
        cards = available_trades[discord_id]
        for multiverse_id in cards:
            card = cards[multiverse_id]
            full_message += f"{card['count']} copies of {card['name']} from set: {card['expansion']}.\n"

    await ctx.send(full_message)
    


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
