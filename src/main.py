import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import json

from trade_manager import TradeManager

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

trade_manager = TradeManager("users.json")


bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server, {member.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if "shit" in message.content.lower():
        await message.delete()
        await message.channel.send(f"{message.author.mention} - don't use that word")
    
    await bot.process_commands(message)

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

@bot.command()
async def assign(ctx):
    role_name = ctx.message.content[ctx.message.content.find(' '):].strip()
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} is now assigned to {role_name}")
    else:
        await ctx.send(f"role does not exist")

@bot.command()
async def unassign(ctx):
    role_name = ctx.message.content[ctx.message.content.find(' '):].strip()
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if role:
        await ctx.author.remove_roles(role)
        await ctx.send(f"{ctx.author.mention} is now unassigned to {role_name}")
    else:
        await ctx.send(f"role does not exist")

@bot.command()
async def login(ctx):
    auth_token = ctx.message.content[ctx.message.content.find(' ') + 1:]
    discord_id = str(ctx.author.id)
    
    # Read users.json
    try:
        with open('users.json', 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"users": {}}
    
    # Check if user id exists, if not add them
    if discord_id not in data.get("users", {}):
        data.setdefault("users", {})[discord_id] = {"echomtg_auth": auth_token}
        trade_manager.add_trader(discord_id, auth_token)
        
        # Write back to users.json
        with open('users.json', 'w') as f:
            json.dump(data, f, indent=4)
        
        await ctx.send(f"{ctx.author.mention} has been added with token!")
    else:
        await ctx.send(f"{ctx.author.mention} already exists in the system!")

@bot.command()
async def search(ctx):
    card_name = ctx.message.content[ctx.message.content.find(' ') + 1:]
    available_trades = trade_manager.search_for_card(card_name)

    for discord_id in available_trades:
        discord_user = bot.get_user(int(discord_id))
        await ctx.send(f"{discord_user.mention} has available trades: ")
        cards = available_trades[discord_id]
        for multiverse_id in cards:
            card = cards[multiverse_id]
            await ctx.send(f"{card['count']} copies of {card['name']} from set: {card['expansion']}.")


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
