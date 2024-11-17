import multiprocessing
import signal
from app import create_app, db
from app.utilities.bot import start_bot

app = create_app()

def run_bot():
    # This function will run in a separate process
    start_bot()

def handle_shutdown(signal, frame):
    print("Shutting down gracefully...")
    # You can add any other shutdown tasks here, such as closing DB connections or stopping the bot
    exit(0)  # Exit the program

if __name__ == "__main__":
    # Set up the signal handler
    signal.signal(signal.SIGINT, handle_shutdown)  # Handle Ctrl+C termination

    # Create the Flask app context
    with app.app_context():
        db.create_all()  # Create tables in the database
    
    # Start the bot in a separate process
    bot_process = multiprocessing.Process(target=run_bot)
    # bot_process.start()

    # Run the Flask app
    app.run(debug=True, use_reloader=False)  # use_reloader=False to avoid double execution
