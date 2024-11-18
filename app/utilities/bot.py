from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from app.models.models import Settings, User
from app import create_app, db

flask_app = create_app()
flask_app.app_context().push()

def get_token():
    print("Attempting to fetch the bot token...")
    with flask_app.app_context():
        setting = Settings.query.filter_by(setting_key="telegram_bot_api_key").first()
        if setting and setting.setting_value:
            print(f"Bot token found: {setting.setting_value}")
            return setting.setting_value
        else:
            print("Error: Telegram Bot API key is not set in the database.")
            raise ValueError("Telegram Bot API key is not set in the database.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    print(f"User ID: {user_id}")
    # Update the message to prompt the user to use /verify
    await update.message.reply_text(
        "Hello! Welcome to the bot. To get started, please verify your email by typing /verify."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - List available commands\n"
        "/verify - Link your email address"
    )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Verify Email", callback_data="verify_email")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Click the button below to verify your email address:", 
        reply_markup=reply_markup
    )

# Callback handler for the Verify button
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "verify_email":
        await query.edit_message_text("Please type your email address:")
        # Save state to track user input
        context.user_data["awaiting_email"] = True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Step 1: If awaiting email
    if context.user_data.get("awaiting_email"):

        # Capture the email
        email = update.message.text
        context.user_data["email"] = email  # Save email to user data
        
        # Step 2: Validate the email
        with flask_app.app_context():
            user = User.query.filter_by(email=email).first()

            # Debugging: Print the retrieved user object to ensure the email exists
            if user:
                print(f"User found: {user.id}, {user.email}")
            else:
                print("User not found in the database.")

            if user is None:
                # If email is not found, notify the user and reset the state
                await update.message.reply_text("❌ Email not found in the system. Please use /verify again with a valid email.")
                context.user_data["awaiting_email"] = False  # Reset state
                context.user_data["awaiting_password"] = False
            else:
                if user.role_id == '5':  # Check if the user is a student (role_id 5)
                    await update.message.reply_text("❌ It seems you're a student. You cannot link a Telegram account for this action. Please use /verify again with a valid email.")
                    context.user_data["awaiting_email"] = False  # Reset the email state
                    context.user_data["awaiting_password"] = False  # Reset the password state
                    context.user_data["user"] = None  # Clear user object from context
                    return  # Exit the function to stop the verification process for students
                
                # If email exists and the user is not a student, ask for the password
                await update.message.reply_text("Please type your password:")
                context.user_data["awaiting_email"] = False  # Clear email state once email is verified
                context.user_data["awaiting_password"] = True  # Change state to awaiting password
                context.user_data["user"] = user  # Save the user object to context for password verification
                print(f"User object stored in context: {context.user_data.get('user')}")
                # Optionally delete the email message if you don't want it cluttering up
                await update.message.delete()

    # Step 3: If awaiting password
    elif context.user_data.get("awaiting_password"):
        print("Checking password...")
        # Capture the password
        password = update.message.text
        email = context.user_data.get("email")  # Retrieve the saved email
        user = context.user_data.get("user")  # Retrieve the saved user object
        user_id = update.message.from_user.id

        # Debugging: Check user and password
        if user:  # Ensure user is not None (from the previous email check)
            print(f"User found for password check: {user.id}, {user.email}")  # Debug print for user verification

            if (user.password == password):  # Check if password is valid
                print("Password matches.")
                # Commit changes within the Flask app context
                with flask_app.app_context():  # Ensure app context is pushed
                    user = User.query.filter_by(email=email).first()
                    user.telegram_id = user_id
                    print("Committing changes to the database...")
                    # Link the Telegram ID if both email and password are correct
                    print(f"Setting telegram_id: {user.telegram_id}")  # Debug print to check the ID being set
                    db.session.commit()  # Commit changes to the database

                # Clear the state after successful verification
                context.user_data["awaiting_email"] = False
                context.user_data["awaiting_password"] = False
                context.user_data["user"] = None  # Clear saved user object after successful verification
                await update.message.reply_text("✅ Verification successful! Your email and password have been linked.")
                # Delete the password message after checking
                await update.message.delete()
            else:
                # If password is incorrect, prompt the user to start over with /verify
                print("Incorrect password.")
                await update.message.reply_text("❌ Incorrect password. Please use /verify to try again.")
                # Clear the state to force the user to restart the verification
                context.user_data["awaiting_email"] = False
                context.user_data["awaiting_password"] = False
                context.user_data["user"] = None  # Clear saved user object
                await update.message.delete()  # Delete the incorrect password message
        else:
            print("No user object found in context!")
            await update.message.reply_text("❌ No user found. Please restart the verification process with /verify.")
            context.user_data["awaiting_email"] = False
            context.user_data["awaiting_password"] = False

    else:
        await update.message.reply_text("I didn't understand that. Use /help for a list of commands.")


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
        app.add_handler(CommandHandler("verify", verify))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Start the bot with polling
        app.run_polling()

    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    start_bot()
