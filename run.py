import asyncio
import signal
from threading import Thread
from app import create_app, db
from app.utilities.bot import start_bot

app = create_app()

def run_bot():
    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)  # Set this loop as the current event loop
    
    # Now run the bot in the event loop
    start_bot()

def handle_shutdown(signal, frame):
    print("Shutting down gracefully...")
    # You can add any other shutdown tasks here, such as closing DB connections or stopping the bot
    exit(0)  # Exit the program

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables in the database
    
    # Start the bot in a separate thread
    bot_thread = Thread(target=run_bot)
    bot_thread.daemon = True  # Allow the bot thread to exit when the main program exits
    bot_thread.start()

    # Set up graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown)  # Handle Ctrl+C termination

    # Run the Flask app
    app.run(debug=True, use_reloader=False)  # use_reloader=False to avoid double execution
