import os
import sys

# Discord Bot Token & OAuth2 credentials for Discord Activity
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")

# Web Server & Activity Port
WEB_PORT = int(os.getenv("PORT", 31378))

# Test Guild IDs for instant slash command synchronization
GUILD_IDS = [int(x.strip()) for x in os.getenv("GUILD_IDS", "").split(",") if x.strip()]
