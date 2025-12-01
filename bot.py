from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Define the function that will be called when the /start command is issued
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_text(f'Bot is alive, {user.first_name}!\n\nComing soon...\n\n© @Super_botz')

def main() -> None:
    """Start the bot."""
    # Replace 'YOUR_API_TOKEN' with your actual API token
    TOKEN = 'Place your bot token here ' 

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Register the command handler for "/start"
    application.add_handler(CommandHandler("start", start))

    # Run the bot using polling. This will keep the bot running and checking for new messages.
    logging.info("Bot is starting polling...")
    application.run_polling(poll_interval=2)

if __name__ == '__main__':
    main()
