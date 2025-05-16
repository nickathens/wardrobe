# wardrobe

This project provides a simple Flask application demonstrating user registration
and login using multiple methods:

- **Email & Password**: Standard registration with an email address and password.
- **Phone Number**: Register with a phone number only.
- **Google Login**: OAuth2 authentication via Google.
- **Facebook Login**: OAuth2 authentication via Facebook.

The sample code stores user information in memory for demonstration purposes.
In a real application you would persist users in a database and add proper
security considerations such as password hashing.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment variables for OAuth providers:
   - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
   - `FACEBOOK_CLIENT_ID` and `FACEBOOK_CLIENT_SECRET`
   - `FLASK_SECRET` for Flask session management
3. Run the application:
   ```bash
   python app.py
   ```

The app will start on `http://127.0.0.1:5000/`.
