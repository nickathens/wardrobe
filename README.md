# Wardrobe

This project provides a simple Flask application that allows users to upload an
image or provide a text description to receive outfit suggestions.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the development server:

```bash
FLASK_DEBUG=1 python app.py
```

Set `FLASK_DEBUG` to `1` to enable debug mode. Omit the variable or set it to `0`
to run without debug features.

For production deployments you should run the application with a WSGI server
such as Gunicorn:

```bash
gunicorn -w 4 app:app
```

Then visit `http://localhost:5000` in your browser.
