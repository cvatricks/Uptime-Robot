import logging
from pyrogram import Client, filters
from pyrogram.types import Message

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# --- CONFIGURATION ---
# 1. Get these from https://my.telegram.org/apps
API_ID = 12345678          # Replace with your integer API ID
API_HASH = 'your_api_hash' # Replace with your string API Hash

# 2. Get this from @BotFather
BOT_TOKEN = 'YOUR_BOT_TOKEN'

# 3. Your Log Channel ID (Make sure the bot is an ADMIN there)
LOG_CHANNEL_ID = -1001234567890 
# ---------------------

# Initialize the Client
app = Client(
    "my_super_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# --- HANDLER GROUP 1: User Interaction ---
# These handlers interact with the user directly.

@app.on_message(filters.command("start") & filters.private, group=1)
async def start_command(client: Client, message: Message):
    """Handle the /start command."""
    user_first_name = message.from_user.first_name
    await message.reply_text(
        f"Bot is alive, {user_first_name}!\n\nComing soon...\n\n© @Super_botz"
    )

@app.on_message(filters.text & ~filters.command & filters.private, group=1)
async def reply_to_text(client: Client, message: Message):
    """Reply to all text messages that are not commands."""
    user_first_name = message.from_user.first_name or "User"
    logging.info(f"Received text from {user_first_name}: {message.text}")
    
    await message.reply_text(
        "Thanks for your message! I'm not fully configured yet.\n\nComing soon...\n\n© @Super_botz"
    )

# --- HANDLER GROUP 2: Logging ---
# This runs PARALLEL to Group 1. Even if Group 1 runs, this will ALSO run.

@app.on_message(filters.all, group=2)
async def log_message(client: Client, message: Message):
    """Forward every single message to the log channel."""
    
    # Basic check to ensure we don't try to forward if ID isn't set
    if not LOG_CHANNEL_ID or LOG_CHANNEL_ID == -1001234567890:
        return

    try:
        # In Pyrogram, the method is .forward()
        await message.forward(chat_id=LOG_CHANNEL_ID)
        logging.info(f"Forwarded message {message.id} to log channel.")
    except Exception as e:
        logging.error(f"Failed to log message: {e}")

# Start the bot
if __name__ == "__main__":
    logging.info("Bot is starting...")
    app.run()
