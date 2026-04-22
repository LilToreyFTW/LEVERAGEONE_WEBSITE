from flask import Flask, request, jsonify, redirect, session, render_template_string
from flask_cors import CORS
import requests
import discord
import os

app = Flask(__name__)
CORS(app)
app.secret_key = "your-secret-key-here"

# Discord OAuth2 Configuration
CLIENT_ID = "1496481098077569115"
CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
if not CLIENT_SECRET:
    try:
        with open('config.txt', 'r') as f:
            lines = f.read().strip().split('\n')
            CLIENT_SECRET = lines[1] if len(lines) > 1 else None
    except FileNotFoundError:
        print("Error: Client secret not found. Set DISCORD_CLIENT_SECRET environment variable or create config.txt")
        exit(1)

REDIRECT_URI = "http://localhost:5000/callback"
DISCORD_API_URL = "https://discord.com/api/v10"
GUILD_ID = "1496479673289543792"
ACCESS_ROLE_ID = "1496480556827938937"
BANNED_USER_ID = 188637276803301376

# Discord invite link
DISCORD_INVITE = "https://discord.gg/WandDv9Jgp"

@app.route('/')
def home():
    return "Discord Auth Server Running"

@app.route('/auth/discord')
def discord_auth():
    """Redirect to Discord OAuth2"""
    return redirect(f"https://discord.com/api/oauth2/authorize"
                   f"?client_id={CLIENT_ID}"
                   f"&redirect_uri={REDIRECT_URI}"
                   f"&response_type=code"
                   f"&scope=identify%20guilds.members.read")

@app.route('/callback')
def callback():
    """Handle Discord OAuth2 callback"""
    code = request.args.get('code')
    if not code:
        return "Error: No code provided", 400
    
    # Exchange code for access token
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(f"{DISCORD_API_URL}/oauth2/token", data=data, headers=headers)
    
    if response.status_code != 200:
        return "Error: Failed to get access token", 400
    
    token_data = response.json()
    access_token = token_data['access_token']
    
    # Get user info
    user_response = requests.get(f"{DISCORD_API_URL}/users/@me", 
                                  headers={'Authorization': f'Bearer {access_token}'})
    
    if user_response.status_code != 200:
        return "Error: Failed to get user info", 400
    
    user_data = user_response.json()
    user_id = user_data['id']
    
    # Check if user is banned
    if int(user_id) == BANNED_USER_ID:
        return render_template_string("""
        <html>
        <head><title>Access Denied</title></head>
        <body>
            <h1>Access Denied</h1>
            <p>You have been banned from this service.</p>
        </body>
        </html>
        """)
    
    # Get user's roles in the guild
    guild_response = requests.get(
        f"{DISCORD_API_URL}/users/@me/guilds/{GUILD_ID}/member",
        headers={'Authorization': f'Bearer {access_token}'}
    )
    
    if guild_response.status_code != 200:
        # User not in guild, redirect to invite
        return redirect(DISCORD_INVITE)
    
    guild_member = guild_response.json()
    roles = guild_member.get('roles', [])
    
    # Check if user has access role
    if ACCESS_ROLE_ID in roles:
        session['user_id'] = user_id
        session['has_access'] = True
        return redirect("http://localhost:3000?auth=success")
    else:
        return redirect(DISCORD_INVITE)

@app.route('/api/check-access')
def check_access():
    """API endpoint to check if user has access"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'access': False, 'reason': 'No user_id provided'}), 400
    
    # Check if user is banned
    if int(user_id) == BANNED_USER_ID:
        return jsonify({'access': False, 'reason': 'User is banned'}), 403
    
    # Check Discord roles
    try:
        guild_response = requests.get(
            f"{DISCORD_API_URL}/guilds/{GUILD_ID}/members/{user_id}",
            headers={'Authorization': f'Bot {os.getenv("DISCORD_BOT_TOKEN") or open("config.txt").read().strip()}'}
        )
        
        if guild_response.status_code == 200:
            guild_member = guild_response.json()
            roles = guild_member.get('roles', [])
            
            if ACCESS_ROLE_ID in roles:
                return jsonify({'access': True})
            else:
                return jsonify({'access': False, 'reason': 'Missing access role'}), 403
        else:
            return jsonify({'access': False, 'reason': 'User not in guild'}), 403
    except Exception as e:
        return jsonify({'access': False, 'reason': str(e)}), 500

@app.route('/api/verify-session')
def verify_session():
    """Verify if current session has access"""
    if session.get('has_access'):
        return jsonify({'access': True, 'user_id': session.get('user_id')})
    return jsonify({'access': False}), 401

if __name__ == '__main__':
    app.run(debug=True, port=5000)
