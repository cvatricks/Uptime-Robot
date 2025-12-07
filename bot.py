import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# --- CONFIGURATION ---

# 1. Set your SINGLE log channel ID here
# Bot(s) MUST be an admin in this channel.
LOG_CHANNEL_ID = -1123456778 # <-- !!! SET THIS !!!

# 2. Add all your bot credentials here
# You can add as many bots as you want to this list.
BOT_CONFIGS = [
    {
        "session_name": "bot1_session",
        "api_id": 123456,         # <-- Bot 1 API ID
        "api_hash": "abcdefghijklmn", # <-- Bot 1 API Hash
        "bot_token": "abcdefghijklmn"    # <-- Bot 1 Token
    },
    {
        "session_name": "bot2_session",
        "api_id": 123456,         # <-- Bot 2 API ID
        "api_hash": "abcdefghijklmn", # <-- Bot 2 API Hash
        "bot_token": "abcdefghijklmn"    # <-- Bot 2 Token
    },
    # {
    #     "session_name": "bot3_session",
    #     "api_id": 11111111,
    #     "api_hash": "api_hash_for_bot_3",
    #     "bot_token": "token_for_bot_3"
    # },
]
# ---------------------


# --- UNIVERSAL HANDLER FUNCTIONS ---
# These functions will be used by *all* bots.

@filters.command("start") & filters.private
async def start_command(client: Client, message: Message):
    """Handle the /start command."""
    user_first_name = message.from_user.first_name
    await message.reply_text(
        f"Bot is alive, {user_first_name}!\n\nComing soon...\n\n© @Super_botz"
    )

@filters.text & ~filters.command & filters.private
async def reply_to_text(client: Client, message: Message):
    """Reply to all text messages that are not commands."""
    user_first_name = message.from_user.first_name or "User"
    logging.info(f"Received text for bot @{client.me.username} from {user_first_name}: {message.text}")
    
    await message.reply_text(
        "Thanks for your message! I'm not fully configured yet.\n\nComing soon...\n\n© @Super_botz"
    )

@filters.all
async def log_message(client: Client, message: Message):
    """Forward every single message to the *single* log channel."""
    
    if not LOG_CHANNEL_ID or LOG_CHANNEL_ID == -1001234567890:
        if "1234567890" in str(LOG_CHANNEL_ID): # Check for placeholder
            logging.warning("LOG_CHANNEL_ID is not set. Skipping message logging.")
        return

    try:
        # Forward the message to the one and only log channel
        await message.forward(chat_id=LOG_CHANNEL_ID)
        
        # Add the bot's username to the console log so you know *which bot* forwarded it
        logging.info(f"Bot @{client.me.username} forwarded message {message.id} to log channel {LOG_CHANNEL_ID}.")
    except Exception as e:
        logging.error(f"Failed to log message for @{client.me.username}: {e}")

# --- Main execution ---
async def main():
    """Initializes, registers handlers, and runs all bots from config."""
    
    clients = []
    
    # Loop through the config and create a Client for each bot
    for config in BOT_CONFIGS:
        # Basic check for placeholder values
        if "token_for_bot" in config["bot_token"] or "12345678" in str(config["api_id"]):
            logging.warning(f"Skipping config for {config['session_name']} due to placeholder values.")
            continue
            
        logging.info(f"Initializing client: {config['session_name']}")
        app = Client(
            name=config["session_name"],
            api_id=config["api_id"],
            api_hash=config["api_hash"],
            bot_token=config["bot_token"]
        )
        
        # --- Register Handlers for this bot ---
        # Group 1 for user replies
        app.on_message(start_command, group=1)
        app.on_message(reply_to_text, group=1)
        
        # Group 2 for logging (runs in parallel)
        app.on_message(log_message, group=2)
        
        clients.append(app)

    if not clients:
        logging.critical("No valid bot configurations found. Please check BOT_CONFIGS. Exiting.")
        return

    try:
        logging.info(f"Starting {len(clients)} client(s)...")
        
        # Create a list of tasks for starting all clients
        start_tasks = [client.start() for client in clients]
        await asyncio.gather(*start_tasks)
        
        logging.info("All clients started successfully. Idling...")
        await asyncio.Event().wait() # Keep the script alive
        
    except KeyboardInterrupt:
        logging.info("Shutdown signal received.")
    finally:
        logging.info("Stopping all clients...")
        
        # Create a list of tasks for stopping all clients
        stop_tasks = [client.stop() for client in clients if client.is_connected]
        await asyncio.gather(*stop_tasks)
        
        logging.info("All clients stopped.")

if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())
