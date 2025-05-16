from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)

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

@app.route('/suggest', methods=['POST'])
def suggest():
    description = request.form.get('description', '')
    suggestions = [f"Outfit suggestion for: {description}"]
    return jsonify({'suggestions': suggestions})

if __name__ == '__main__':
    app.run(debug=True)
