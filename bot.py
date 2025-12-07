import logging
import asyncio
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from pyrogram.enums import ParseMode, ChatMemberStatus, ChatType

# --- IMPORT CONFIGURATION AND TRANSLATION ---
try:
    from config import LOG_CHANNEL_ID, BOT_CONFIGS, AUTH_CHANNEL
    from translation import AUTH_CHANNEL_TEXT, AUTH_CHANNEL_MARKUP_TEXT
except ImportError:
    logging.critical("Config or Translation files are missing or variables are incorrect. Exiting.")
    exit(1)
# ------------------------------------------

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


# --- CUSTOM FILTER FUNCTION ---
# This filter reliably checks if a message is private text and NOT a command.
def non_command_text(flt, client, message):
    """Filter that returns True for private text messages that are NOT commands."""
    if message.text is None:
        return False
    
    is_private = message.chat.type == ChatType.PRIVATE
    # Explicitly check if the text does not start with the command prefix '/'
    is_not_command = not message.text.startswith('/')
    
    return is_private and is_not_command


# --- CORE UTILITY FUNCTION (Force Subscribe Check) ---

async def check_channel_subscription(client: Client, message: Message) -> bool:
    """
    Checks if the user is a member of the AUTH_CHANNEL using a robust status check.
    
    Returns: True if subscribed (creator/admin/member), False otherwise.
    """
    if not AUTH_CHANNEL or AUTH_CHANNEL == -1001987654321:
        logging.warning(f"AUTH_CHANNEL is not configured for bot @{client.me.username}. Skipping subscription check.")
        return True
        
    user_id = message.from_user.id
    
    try:
        member = await client.get_chat_member(chat_id=AUTH_CHANNEL, user_id=user_id)
        
        # Define what constitutes a "subscribed" status
        subscribed_statuses = [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]
        
        if member.status not in subscribed_statuses:
            # If the user is found but their status is left, kicked, restricted, etc.,
            # we manually raise to trigger the prompt message.
            raise UserNotParticipant
            
    except UserNotParticipant:
        # This block catches both the API's exception (user not found/never joined) 
        # and our manual raise (user found but not subscribed/left/kicked).
        await client.send_message(
            chat_id=message.chat.id,
            text=AUTH_CHANNEL_TEXT,
            parse_mode=ParseMode.HTML,
            reply_to_message_id=message.id,
            reply_markup=InlineKeyboardMarkup(
                               [
                                   [   InlineKeyboardButton(text=AUTH_CHANNEL_MARKUP_TEXT, url="https://t.me/Super_botz")
                                   ]
                               ]
            )
        )
        return False
    except Exception as e:
        # Catch all other exceptions (e.g., bot not admin in channel, channel not found)
        logging.error(f"Subscription check failed due to API error for user {user_id}: {e}")
        # When in doubt, allow the user to proceed to prevent bot outage
        return True 

    # If the user is found and their status is in subscribed_statuses
    return True


# --- UNIVERSAL HANDLER FUNCTIONS ---

async def start_command(client: Client, message: Message):
    """Handle the /start command."""
    
    # 1. Mandatory subscription check
    if not await check_channel_subscription(client, message):
        return
        
    user_first_name = message.from_user.first_name
    await message.reply_text(
        f"Bot is alive, {user_first_name}! Access granted.\n\nBot is under maintenance\n\n© @Super_botz"
    )

async def reply_to_text(client: Client, message: Message):
    """Reply to all non-command text messages."""

    # 1. Mandatory subscription check
    if not await check_channel_subscription(client, message):
        return
        
    user_first_name = message.from_user.first_name or "User"
    logging.info(f"Received text for bot @{client.me.username} from {user_first_name}: {message.text}")
    
    await message.reply_text(
        "Bot is under maintenance."
    )

async def log_message(client: Client, message: Message):
    """Forward every single message to the *single* log channel."""
    
    if "1001234567890" in str(LOG_CHANNEL_ID): 
        logging.warning("LOG_CHANNEL_ID is set to placeholder. Skipping message logging.")
        return

    try:
        # Group 2 handles logging, which should happen regardless of user access
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

    non_command_filter_obj = filters.create(non_command_text)

    for config in valid_configs:
        logging.info(f"Initializing client: {config['session_name']}")
        app = Client(
            name=config["session_name"],
            api_id=config["api_id"],
            api_hash=config["api_hash"],
            bot_token=config["bot_token"]
        )
        
        # --- Register Handlers ---
        
        # Group 1 (Access-controlled actions)
        app.add_handler(
            MessageHandler(start_command, filters=filters.command("start") & filters.private),
            group=1
        )
        app.add_handler(
            MessageHandler(reply_to_text, filters=non_command_filter_obj),
            group=1
        )
        
        # Group 2 (Logging, runs in parallel and is NOT access-controlled)
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
