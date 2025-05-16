from flask import Flask, request, redirect, url_for, session, jsonify
from authlib.integrations.flask_client import OAuth
import os

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET', 'change-me')

# OAuth configuration
oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

facebook = oauth.register(
    name='facebook',
    client_id=os.getenv('FACEBOOK_CLIENT_ID'),
    client_secret=os.getenv('FACEBOOK_CLIENT_SECRET'),
    access_token_url='https://graph.facebook.com/v10.0/oauth/access_token',
    access_token_params=None,
    authorize_url='https://www.facebook.com/v10.0/dialog/oauth',
    authorize_params=None,
    api_base_url='https://graph.facebook.com/',
    client_kwargs={'scope': 'email'},
)

# In-memory storage for demo purposes
USERS = {}

@app.post('/register/email')
def register_email():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return {'error': 'email and password required'}, 400
    if email in USERS:
        return {'error': 'user already exists'}, 400
    USERS[email] = {'password': password, 'method': 'email'}
    return {'status': 'registered'}

@app.post('/register/phone')
def register_phone():
    data = request.json or {}
    phone = data.get('phone')
    if not phone:
        return {'error': 'phone required'}, 400
    if phone in USERS:
        return {'error': 'user already exists'}, 400
    USERS[phone] = {'method': 'phone'}
    return {'status': 'registered'}

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/authorize')
def authorize_google():
    token = google.authorize_access_token()
    userinfo = google.parse_id_token(token)
    session['user'] = userinfo
    return jsonify(userinfo)

@app.route('/login/facebook')
def login_facebook():
    redirect_uri = url_for('authorize_facebook', _external=True)
    return facebook.authorize_redirect(redirect_uri)

@app.route('/login/facebook/authorize')
def authorize_facebook():
    token = facebook.authorize_access_token()
    resp = facebook.get('me?fields=id,name,email')
    userinfo = resp.json()
    session['user'] = userinfo
    return jsonify(userinfo)

if __name__ == '__main__':
    app.run(debug=True)
