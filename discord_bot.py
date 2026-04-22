import discord
from discord.ext import commands
import asyncio
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from urllib.parse import urlparse, parse_qs

# Configuration
BANNED_USER_ID = 188637276803301376
BANNED_USER_IDS = [188637276803301376, 970868561956442142, 665395008429621288, 471795129867567134, 715242202476839075, 630149736334360591, 659842257561583622]

# Initial allowed IDs (will be loaded from file if exists)
INITIAL_ALLOWED_IDS = [
    215279117111656448,
    304789212224552972,
    892435951341695007,
    782760874313515010,
    531972745672523777,
    764199593956737064,
    1496480219476004994,
    1368087024401252393,  # Owner
    219570005744812033
]

ALLOWED_DISCORD_IDS_FILE = "allowed_discord_ids.json"

def load_allowed_ids():
    """Load allowed IDs from file"""
    try:
        with open(ALLOWED_DISCORD_IDS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create file with initial IDs
        with open(ALLOWED_DISCORD_IDS_FILE, 'w') as f:
            json.dump(INITIAL_ALLOWED_IDS, f)
        return INITIAL_ALLOWED_IDS.copy()
    except Exception as e:
        print(f"Error loading allowed IDs: {e}")
        return INITIAL_ALLOWED_IDS.copy()

def save_allowed_ids():
    """Save allowed IDs to file"""
    try:
        with open(ALLOWED_DISCORD_IDS_FILE, 'w') as f:
            json.dump(ALLOWED_DISCORD_IDS, f)
        print(f"Saved {len(ALLOWED_DISCORD_IDS)} allowed IDs to file")
    except Exception as e:
        print(f"Error saving allowed IDs: {e}")

ALLOWED_DISCORD_IDS = load_allowed_ids()
print(f"Loaded {len(ALLOWED_DISCORD_IDS)} allowed IDs from file")

ACCESS_ROLE_ID = 1496480556827938937
OWNER_ROLE_ID = 1496480219476004994
GUILD_ID = 1496479673289543792

# Logging channels (replace with actual channel IDs)
LOGS_CHANNEL_ID = None  # Set to your logs channel ID
VERIFICATION_CHANNEL_ID = None  # Set to your verification channel ID

async def send_log(channel_id, title, description, color=0x00ff00):
    """Send a log message to a Discord channel"""
    if not channel_id:
        print(f"Log channel not set, skipping log: {title}")
        return
    
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print(f"Guild not found, skipping log: {title}")
        return
    
    channel = guild.get_channel(channel_id)
    if not channel:
        print(f"Channel {channel_id} not found, skipping log: {title}")
        return
    
    try:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=f"LeverageONE Bot - {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        await channel.send(embed=embed)
        print(f"Logged to channel {channel_id}: {title}")
    except Exception as e:
        print(f"Error sending log: {e}")

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
    """Auto-ban if user is on banned list, auto-add if has ACCESS role"""
    # Check if user is banned
    if member.id in BANNED_USER_IDS:
        try:
            await member.guild.ban(member, reason="Banned from system")
            print(f"Auto-banned user {member.id} on join")
        except Exception as e:
            print(f"Error auto-banning user: {e}")
        return
    
    # Check if user has ACCESS role and add to allowed list
    access_role = member.guild.get_role(ACCESS_ROLE_ID)
    if access_role and access_role in member.roles:
        if member.id not in ALLOWED_DISCORD_IDS:
            ALLOWED_DISCORD_IDS.append(member.id)
            save_allowed_ids()
            print(f"Auto-added user {member.id} to allowed list on join (has ACCESS role)")

@bot.event
async def on_member_update(before, after):
    """Handle role changes - auto-add if user gets ACCESS role"""
    # Check if roles changed
    if len(before.roles) != len(after.roles) or set(before.roles) != set(after.roles):
        access_role = after.guild.get_role(ACCESS_ROLE_ID)
        
        # Check if user gained ACCESS role
        if access_role and access_role in after.roles and access_role not in before.roles:
            if after.id not in ALLOWED_DISCORD_IDS:
                ALLOWED_DISCORD_IDS.append(after.id)
                save_allowed_ids()
                print(f"Auto-added user {after.id} to allowed list (gained ACCESS role)")
        
        # Check if user lost ACCESS role
        elif access_role and access_role in before.roles and access_role not in after.roles:
            if after.id in ALLOWED_DISCORD_IDS:
                ALLOWED_DISCORD_IDS.remove(after.id)
                save_allowed_ids()
                print(f"Auto-removed user {after.id} from allowed list (lost ACCESS role)")

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

# HTTP API Server for role verification
class VerificationHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        
        if parsed_path.path == '/verify':
            query = parse_qs(parsed_path.query)
            discord_id = query.get('discord_id', [None])[0]
            
            if not discord_id:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing discord_id parameter'}).encode())
                return
            
            try:
                discord_id_int = int(discord_id)
            except ValueError:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid discord_id format'}).encode())
                return
            
            # Check if user is banned
            if discord_id_int in BANNED_USER_IDS:
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'access': False, 'reason': 'User is banned'}).encode())
                return
            
            # Check if user is in guild and has access role
            guild = bot.get_guild(GUILD_ID)
            if not guild:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Guild not found'}).encode())
                return
            
            try:
                member = guild.get_member(discord_id_int)
                if not member:
                    # User not in guild
                    self.send_response(403)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'access': False, 'reason': 'User not in Discord server'}).encode())
                    return
                
                # Check if user has access role
                access_role = guild.get_role(ACCESS_ROLE_ID)
                if access_role in member.roles:
                    # Log verification
                    asyncio.create_task(send_log(
                        VERIFICATION_CHANNEL_ID,
                        f"🔐 User Verified",
                        f"**Discord ID:** {discord_id_int}\n**Username:** {member.name}\n**Timestamp:** {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
                        color=0x5763719
                    ))
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'access': True, 'discord_id': str(discord_id_int), 'username': member.name}).encode())
                else:
                    self.send_response(403)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'access': False, 'reason': 'User does not have access role'}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        
        elif parsed_path.path == '/log_download':
            query = parse_qs(parsed_path.query)
            discord_id = query.get('discord_id', [None])[0]
            username = query.get('username', [None])[0]
            
            # Log download
            asyncio.create_task(send_log(
                LOGS_CHANNEL_ID,
                f"📥 Download Clicked",
                f"**Discord ID:** {discord_id or 'Unknown'}\n**Username:** {username or 'Unknown'}\n**Timestamp:** {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n**Source:** Proton Drive",
                color=0x5763719
            ))
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def run_http_server():
    server = HTTPServer(('localhost', 5001), VerificationHandler)
    print("HTTP API Server running on http://localhost:5001")
    server.serve_forever()

if __name__ == "__main__":
    # Start HTTP server in a separate thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Run Discord bot
    bot.run(TOKEN)
