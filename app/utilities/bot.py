from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from app.models.models import Settings
from app import create_app
from flask import current_app

# BOT_TOKEN = "7847944580:AAHCmXpY4oJa3OvzIpJc7ANfiSFFL_21FIA"
flask_app = create_app()

def get_token():
    print("Attempting to fetch the bot token...")
    with flask_app.app_context():  # Ensures the app context is available
        setting = Settings.query.filter_by(setting_key="telegram_bot_api_key").first()
        if setting and setting.setting_value:
            print(f"Bot token found: {setting.setting_value}")
            return setting.setting_value
        else:
            print("Error: Telegram Bot API key is not set in the database.")
            raise ValueError("Telegram Bot API key is not set in the database.")

async def send_custom_message(context: ContextTypes.DEFAULT_TYPE):
    user_id = 7076947123  
    due_date = "2024-11-15"
    amount_due = 150.00
    message = f"⚠️ *Payment Due Notification*\n\n" \
              f"Dear user, you have a payment of ${amount_due} due on {due_date}. " \
              f"Please make your payment to avoid any late fees."
    await context.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    print(f"User ID: {user_id}")
    await update.message.reply_text("Hello! Welcome to the bot. Type /help for commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Available commands:\n/start - Start the bot\n/help - List commands")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await update.message.reply_text(f"You said: {user_message}")

# Rename 'main' to 'start_bot' here
def start_bot():
    try:
        print("Attempting to retrieve the bot token...")
        BOT_TOKEN = get_token()  # Will raise ValueError if token is not found
        print(f"Using Bot Token: {BOT_TOKEN}")
        app = Application.builder().token(BOT_TOKEN).build()

        # Add handlers for start and help commands, and for generic text messages
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Schedule a job to send a message to a specific user immediately after the bot starts
        app.job_queue.run_once(send_custom_message, 0)

        # Start the bot with polling
        app.run_polling()

    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    start_bot()