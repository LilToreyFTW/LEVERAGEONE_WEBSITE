# LeverageONE Website - Discord Authentication

This website requires Discord authentication to access the download. Users must join the Discord server and have the ACCESS role to download LeverageONE.

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create config.txt

Create a `config.txt` file with your Discord bot token and client secret:

```
YOUR_DISCORD_BOT_TOKEN
YOUR_DISCORD_CLIENT_SECRET
```

Or set environment variables:
- `DISCORD_BOT_TOKEN`
- `DISCORD_CLIENT_SECRET`

### 3. Run the Discord Bot

The Discord bot handles auto-banning the banned user and role management.

```bash
python discord_bot.py
```

**Bot Features:**
- Auto-bans user ID: 188637276803301376
- Allows specific Discord IDs access
- Owner commands: !ban, !addaccess, !removeaccess
- Verification command: !verify

### 4. Run the Auth Server

The Flask server handles Discord OAuth2 authentication.

```bash
python discord_auth.py
```

The server runs on http://localhost:5000

### 5. Open the Website

Open `index.html` in a browser or serve it with a web server.

## Configuration

### Discord Bot Configuration

Edit `discord_bot.py` to modify:
- Banned user ID
- Allowed Discord IDs
- Access role ID
- Bot token (via config.txt or environment variable)

### Auth Server Configuration

Edit `discord_auth.py` to modify:
- Client ID
- Client secret (via config.txt or environment variable)
- Redirect URI
- Guild ID
- Access role ID

## Discord Server Setup

### Auto-Role Configuration

Users who join via the invite link automatically receive the ACCESS role.

**Discord Invite:** https://discord.gg/WandDv9Jgp

**Access Role ID:** 1496480556827938937

**Owner Role ID:** 1496480219476004994

**Guild ID:** 1496479673289543792

### Allowed Discord IDs

- 215279117111656448
- 304789212224552972
- 892435951341695007
- 782760874313515010
- 531972745672523777
- 764199593956737064
- 1496480219476004994 (Owner)

### Banned User

**User ID:** 188637276803301376
This user is automatically banned from both Discord and the website.

## How It Works

1. User visits the website download page
2. User clicks "Join Discord Server" to join the Discord
3. User receives the ACCESS role automatically upon joining
4. User clicks "Verify Discord Access" to verify their role
5. If verified, the download section is revealed
6. User can download LeverageONE with the provided password

## Bot Commands

- `!verify` - Check if user has access role
- `!ban <user_id>` - Ban a user (owner only)
- `!addaccess <user_id>` - Add access role to user (owner only)
- `!removeaccess <user_id>` - Remove access role from user (owner only)

## Security Features

- Auto-ban for specific user ID
- Role-based access control
- Discord OAuth2 authentication
- Session management
- Banned user detection
- Secrets stored in config file (not in code)

## Troubleshooting

**Bot not running:** Make sure the bot token is in config.txt or set as environment variable.

**Auth server not working:** Check that the Flask server is running on port 5000.

**Download not showing:** Ensure the user has the ACCESS role in the Discord server.

**Banned user still accessing:** Check that the banned user ID is correctly configured in both the bot and auth server.
