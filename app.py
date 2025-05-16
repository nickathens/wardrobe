import os
from flask import Flask, request, render_template, jsonify
from schp import SCHPParser
from werkzeug.utils import secure_filename

app = Flask(__name__)
schp_parser = SCHPParser()

# Simple in-memory user store. In a real application this would be a database.
users = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    # In a real application you would process the uploaded file
    file = request.files.get('image')
    if file is None or file.filename == '':
        return jsonify({'error': 'No file provided'}), 400

    filename = secure_filename(file.filename)
    suggestions = [f"Outfit suggestion based on {filename}"]
    return jsonify({'suggestions': suggestions})


@app.route('/parse', methods=['POST'])
def parse_image():
    file = request.files.get('image')
    if file is None or file.filename == '':
        return jsonify({'error': 'No file provided'}), 400

    filename = secure_filename(file.filename)
    # Save the file temporarily to parse.
    temp_path = os.path.join('/tmp', filename)
    file.save(temp_path)
    parts = schp_parser.parse(temp_path)
    os.remove(temp_path)
    return jsonify({'parts': parts})

@app.route('/suggest', methods=['POST'])
def suggest():
    description = request.form.get('description', '')
    suggestions = [f"Outfit suggestion for: {description}"]
    return jsonify({'suggestions': suggestions})


@app.route('/register/email', methods=['POST'])
def register_email():
    email = request.form.get('email')
    password = request.form.get('password')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    users[email] = {'method': 'email', 'password': password}
    return jsonify({'message': f'Registered {email} via email'})


@app.route('/register/phone', methods=['POST'])
def register_phone():
    phone = request.form.get('phone')
    if not phone:
        return jsonify({'error': 'Phone number required'}), 400
    users[phone] = {'method': 'phone'}
    return jsonify({'message': f'Registered {phone} via phone'})


@app.route('/register/google', methods=['POST'])
def register_google():
    token = request.form.get('token')
    if not token:
        return jsonify({'error': 'Google token required'}), 400
    users[token] = {'method': 'google'}
    return jsonify({'message': 'Registered via Google'})


@app.route('/register/facebook', methods=['POST'])
def register_facebook():
    token = request.form.get('token')
    if not token:
        return jsonify({'error': 'Facebook token required'}), 400
    users[token] = {'method': 'facebook'}
    return jsonify({'message': 'Registered via Facebook'})

if __name__ == '__main__':
    flag = os.getenv('FLASK_DEBUG')
    debug_mode = flag.lower() in {'1', 'true', 'yes'} if flag is not None else False
    app.run(debug=debug_mode)
