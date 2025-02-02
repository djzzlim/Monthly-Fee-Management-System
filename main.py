from app import create_app, db
from app.utilities.email import send_email

app = create_app()

if __name__ == "__main__":
    # Run the Flask app
    app.run(debug=True, use_reloader=False)  # use_reloader=False to avoid double execution
