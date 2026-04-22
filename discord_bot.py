import discord
from discord.ext import commands
import asyncio
import json
import os

# Configuration
BANNED_USER_ID = 188637276803301376
ALLOWED_DISCORD_IDS = [
    215279117111656448,
    304789212224552972,
    892435951341695007,
    782760874313515010,
    531972745672523777,
    764199593956737064,
    1496480219476004994  # Owner
]

ACCESS_ROLE_ID = 1496480556827938937
OWNER_ROLE_ID = 1496480219476004994
GUILD_ID = 1496479673289543792

# Load bot token from environment variable or config file
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    try:
        with open('config.txt', 'r') as f:
            TOKEN = f.read().strip()
    except FileNotFoundError:
        print("Error: Bot token not found. Set DISCORD_BOT_TOKEN environment variable or create config.txt")
        exit(1)

# Intents
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user.name}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Guild ID: {GUILD_ID}")
    
    # Check for banned user and ban them
    guild = bot.get_guild(GUILD_ID)
    if guild:
        banned_member = guild.get_member(BANNED_USER_ID)
        if banned_member:
            try:
                await guild.ban(banned_member, reason="Banned from system")
                print(f"Banned user {BANNED_USER_ID} from Discord")
            except discord.Forbidden:
                print(f"Failed to ban user {BANNED_USER_ID} - insufficient permissions")
            except Exception as e:
                print(f"Error banning user: {e}")
        else:
            print(f"Banned user {BANNED_USER_ID} not found in guild")

@bot.event
async def on_member_join(member):
    """Auto-ban if user is on banned list"""
    if member.id == BANNED_USER_ID:
        try:
            await member.guild.ban(member, reason="Banned from system")
            print(f"Auto-banned user {BANNED_USER_ID} on join")
        except Exception as e:
            print(f"Error auto-banning user: {e}")

@bot.command()
async def verify(ctx):
    """Verify if user has access role"""
    access_role = ctx.guild.get_role(ACCESS_ROLE_ID)
    if access_role in ctx.author.roles:
        await ctx.send(f"✅ {ctx.author.mention} has access to download")
    else:
        await ctx.send(f"❌ {ctx.author.mention} does not have access to download")

@bot.command()
async def ban(ctx, user_id: int):
    """Ban a user (owner only)"""
    if ctx.author.id != 1496480219476004994:
        await ctx.send("❌ Only the owner can use this command")
        return
    
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.ban(user, reason="Banned by owner")
        await ctx.send(f"✅ Banned user {user_id}")
    except Exception as e:
        await ctx.send(f"❌ Error banning user: {e}")

@bot.command()
async def addaccess(ctx, user_id: int):
    """Add access role to user (owner only)"""
    if ctx.author.id != 1496480219476004994:
        await ctx.send("❌ Only the owner can use this command")
        return
    
    try:
        member = await ctx.guild.fetch_member(user_id)
        access_role = ctx.guild.get_role(ACCESS_ROLE_ID)
        await member.add_roles(access_role)
        await ctx.send(f"✅ Added access role to {user_id}")
    except Exception as e:
        await ctx.send(f"❌ Error adding access role: {e}")

@bot.command()
async def removeaccess(ctx, user_id: int):
    """Remove access role from user (owner only)"""
    if ctx.author.id != 1496480219476004994:
        await ctx.send("❌ Only the owner can use this command")
        return
    
    try:
        member = await ctx.guild.fetch_member(user_id)
        access_role = ctx.guild.get_role(ACCESS_ROLE_ID)
        await member.remove_roles(access_role)
        await ctx.send(f"✅ Removed access role from {user_id}")
    except Exception as e:
        await ctx.send(f"❌ Error removing access role: {e}")

# Store user access status for website
user_access_cache = {}

def has_access(user_id):
    """Check if user has access (can be called from website)"""
    return user_id in ALLOWED_DISCORD_IDS

def is_banned(user_id):
    """Check if user is banned"""
    return user_id == BANNED_USER_ID

if __name__ == "__main__":
    bot.run(TOKEN)
