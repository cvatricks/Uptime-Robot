import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message


#import pip
#from pip._internal import main as _main

#package_names=['gcc', 'TgCrypto'] #packages to install
#_main(['install'] + package_names + ['--upgrade'])




# --- IMPORT CONFIGURATION ---
try:
    from config import LOG_CHANNEL_ID, BOT_CONFIGS
except ImportError:
    logging.critical("Configuration file (config.py) not found or variables are missing. Exiting.")
    exit(1)
# ----------------------------

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


# --- CUSTOM FILTER FUNCTION ---
# This filter reliably checks if a message is private text and NOT a command.
def non_command_text(flt, client, message):
    """Filter that returns True for private text messages that are NOT commands."""
    if message.text is None:
        return False
    
    is_private = message.chat.type == "private"
    # Explicitly check if the text does not start with the command prefix '/'
    is_not_command = not message.text.startswith('/')
    
    return is_private and is_not_command


# --- UNIVERSAL HANDLER FUNCTIONS ---

async def start_command(client: Client, message: Message):
    """Handle the /start command."""
    user_first_name = message.from_user.first_name
    await message.reply_text(
        f"Bot is alive, {user_first_name}!\n\nComing soon...\n\n© @Super_botz"
    )

async def reply_to_text(client: Client, message: Message):
    """Reply to all non-command text messages."""
    user_first_name = message.from_user.first_name or "User"
    logging.info(f"Received text for bot @{client.me.username} from {user_first_name}: {message.text}")
    
    await message.reply_text(
        "Thanks for your message! I'm not fully configured yet.\n\nComing soon...\n\n© @Super_botz"
    )

async def log_message(client: Client, message: Message):
    """Forward every single message to the *single* log channel."""
    
    if "1001234567890" in str(LOG_CHANNEL_ID): 
        logging.warning("LOG_CHANNEL_ID is set to placeholder. Skipping message logging.")
        return

    try:
        await message.forward(chat_id=LOG_CHANNEL_ID)
        logging.info(f"Bot @{client.me.username} forwarded message {message.id} to log channel {LOG_CHANNEL_ID}.")
    except Exception as e:
        logging.error(f"Failed to log message for @{client.me.username}: {e}")

# --- Main execution ---
async def main():
    """Initializes, registers handlers, and runs all bots from config."""
    
    clients = []
    
    valid_configs = [c for c in BOT_CONFIGS if c.get("bot_token") and c.get("api_id")]
    
    if not valid_configs:
        logging.critical("No valid bot configurations found in config.py. Check tokens and IDs.")
        return

    # Create the custom filter object once
    non_command_filter_obj = filters.create(non_command_text)

    for config in valid_configs:
        logging.info(f"Initializing client: {config['session_name']}")
        app = Client(
            name=config["session_name"],
            api_id=config["api_id"],
            api_hash=config["api_hash"],
            bot_token=config["bot_token"]
        )
        
        # --- Register Handlers using app.add_handler() ---
        
        # Group 1 (Default actions: start, reply)
        app.add_handler(
            MessageHandler(start_command, filters=filters.command("start") & filters.private),
            group=1
        )
        
        # Using the robust custom filter
        app.add_handler(
            MessageHandler(reply_to_text, filters=non_command_filter_obj),
            group=1
        )
        
        # Group 2 (Logging: runs in parallel for ALL message types)
        app.add_handler(
            MessageHandler(log_message, filters=filters.all),
            group=2
        )
        
        clients.append(app)

    try:
        logging.info(f"Starting {len(clients)} client(s)...")
        
        start_tasks = [client.start() for client in clients]
        await asyncio.gather(*start_tasks)
        
        logging.info("All clients started successfully. Idling...")
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logging.info("Shutdown signal received.")
    finally:
        logging.info("Stopping all clients...")
        stop_tasks = [client.stop() for client in clients if client.is_connected]
        await asyncio.gather(*stop_tasks)
        
        logging.info("All clients stopped.")

if __name__ == "__main__":
    asyncio.run(main())
