# Kindergarten Fee Management System

This is a Django-based application for managing the monthly fees of a private kindergarten. The application includes models for managing students, parents, fees, invoices, and users.

## Prerequisites

Make sure you have the following installed:
- Python (>= 3.6)
- Django
- SQLite (optional, included by default in Django)

## Setup Instructions

### 1. Clone the Repository

Clone this repository to your local machine:

```bash
git clone https://github.com/djzzlim/Monthly-Fee-Management-System.git
cd Monthly-Fee-Management-System
```

### 2. Create a Virtual Environment

To avoid dependency conflicts, it's recommended to set up a virtual environment for the project.

On Linux/MacOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

This will activate your virtual environment, and any packages you install now will be isolated from your global Python installation.

### 3. Install Requirements

Make sure your virtual environment is activated, then install the required dependencies:

```bash
pip install -r requirements.txt
```

### 4. Run the Django Development Server

To start the Django server, use the following command:

```bash
python manage.py runserver
```

By default, the server will run at http://127.0.0.1:8000/. Open this URL in your web browser to view the application.

---

### Stopping the Server
To stop the Django server, press Ctrl+C in your terminal.

### Additional Commands
Deactivate Virtual Environment: To deactivate your virtual environment when you're done working on the project, simply run:
```bash
deactivate
```