import os
import logging
import imghdr
import time
try:
    from flask import Flask, request, render_template, jsonify
except Exception:  # pragma: no cover - fallback when Flask isn't installed
    # The stub is only used for running the test suite without real Flask
    from flask_stub import Flask, request, render_template, jsonify
from clothseg import ClothSegmenter
from werkzeug.security import generate_password_hash, check_password_hash
try:
    from sqlalchemy import Column, Integer, String, create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker
except Exception:  # pragma: no cover - fallback when SQLAlchemy isn't installed
    # These stubs allow tests to run without the real dependency
    from sqlalchemy_stub import Column, Integer, String, create_engine
    from sqlalchemy_stub import declarative_base, sessionmaker
try:
    import openai  # type: ignore
except Exception:  # pragma: no cover - fallback when OpenAI package is missing
    # Test environments use a lightweight OpenAI stub
    import openai_stub as openai
import tempfile

openai.api_key = os.getenv("OPENAI_API_KEY")
if openai.api_key is None and getattr(openai, "__name__", "") != "openai_stub":
    raise RuntimeError("OPENAI_API_KEY not set")

app = Flask(__name__)
logger = logging.getLogger(__name__)
cloth_segmenter = ClothSegmenter()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    identifier = Column(String, unique=True, nullable=False)
    method = Column(String, nullable=False)
    password = Column(String)


Base.metadata.create_all(engine)

# Allowed upload types
ALLOWED_EXTENSIONS = {'.png', '.jpg', '.jpeg'}
ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg'}
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2 MB limit
OPENAI_MAX_RETRIES = 3


def _is_allowed_image(file) -> bool:
    """Return True if ``file`` appears to be an allowed image.

    The check verifies the file extension or MIME type, ensures the
    content looks like an actual image using ``imghdr``, and enforces a
    small size limit. The original file pointer is restored before
    returning.
    """

    ext = os.path.splitext(getattr(file, "filename", ""))[1].lower()
    mime = getattr(file, "mimetype", None)
    if ext not in ALLOWED_EXTENSIONS and mime not in ALLOWED_MIME_TYPES:
        return False

    f = getattr(file, "stream", file)
    try:
        pos = f.tell()
    except Exception:  # pragma: no cover - file lacks tell/seek
        pos = None

    try:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0)
    except Exception:  # pragma: no cover - couldn't determine size
        return False

    if size > MAX_IMAGE_SIZE:
        if pos is not None:
            f.seek(pos)
        return False

    try:
        sample = f.read(512)
        f.seek(0)
        kind = imghdr.what(None, sample)
        if kind == "jpeg":
            kind = "jpg"
        if kind not in {"png", "jpg"}:
            if pos is not None:
                f.seek(pos)
            return False
    except Exception:
        if pos is not None:
            f.seek(pos)
        return False

    if pos is not None:
        f.seek(pos)
    return True


def _call_openai_with_retry(func, *args, **kwargs):
    """Call an OpenAI function with basic retry logic."""
    for attempt in range(1, OPENAI_MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except openai.error.OpenAIError:
            if attempt == OPENAI_MAX_RETRIES:
                raise
            logger.warning("OpenAI call failed, retrying (%s/%s)", attempt, OPENAI_MAX_RETRIES)
            time.sleep(0.5)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    # In a real application you would process the uploaded file
    file = request.files.get('image')
    if file is None or file.filename == '':
        return jsonify({'error': 'No file provided'}), 400
    if not _is_allowed_image(file):
        return jsonify({'error': 'Invalid file type'}), 400

    # Save the uploaded file temporarily so it can be parsed.
    tmp = tempfile.NamedTemporaryFile(delete=False)
    temp_path = tmp.name
    tmp.close()
    file.save(temp_path)

    try:
        parts = cloth_segmenter.parse(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    part_names = ", ".join(parts.keys()) if parts else "unknown parts"
    prompt = f"Suggest an outfit based on the clothing parts: {part_names}"
    try:
        chat = _call_openai_with_retry(
            openai.ChatCompletion.create,
            messages=[{"role": "user", "content": prompt}],
            model="gpt-3.5-turbo",
        )
        suggestion_text = chat["choices"][0]["message"]["content"]
        image = _call_openai_with_retry(openai.Image.create, prompt=prompt)
        image_url = image["data"][0]["url"]
    except openai.error.OpenAIError:
        logger.exception("OpenAI request failed")
        return jsonify({"error": "OpenAI request failed"}), 502

    return jsonify({'suggestions': [suggestion_text], 'image_url': image_url})


@app.route('/parse', methods=['POST'])
def parse_image():
    file = request.files.get('image')
    if file is None or file.filename == '':
        return jsonify({'error': 'No file provided'}), 400
    if not _is_allowed_image(file):
        return jsonify({'error': 'Invalid file type'}), 400

    # Save the file temporarily to parse using a unique path.
    tmp = tempfile.NamedTemporaryFile(delete=False)
    temp_path = tmp.name
    tmp.close()
    file.save(temp_path)
    try:
        parts = cloth_segmenter.parse(temp_path)
    except Exception:
        return jsonify({'error': 'Segmentation failed'}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return jsonify({'parts': parts})

@app.route('/suggest', methods=['POST'])
def suggest():
    description = request.form.get('description', '')
    prompt = f"Suggest an outfit for: {description}"
    try:
        chat = _call_openai_with_retry(
            openai.ChatCompletion.create,
            messages=[{"role": "user", "content": prompt}],
            model="gpt-3.5-turbo",
        )
        suggestion_text = chat["choices"][0]["message"]["content"]
        image = _call_openai_with_retry(openai.Image.create, prompt=prompt)
        image_url = image["data"][0]["url"]
    except openai.error.OpenAIError:
        logger.exception("OpenAI request failed")
        return jsonify({"error": "OpenAI request failed"}), 502

    return jsonify({'suggestions': [suggestion_text], 'image_url': image_url})


@app.route('/compose', methods=['POST'])
def compose():
    """Combine a user photo with selected clothing images."""
    body = request.files.get('body')
    clothes = []
    if hasattr(request.files, 'getlist'):
        clothes = request.files.getlist('clothes')
    else:
        for key, value in request.files.items():
            if key.startswith('clothes'):
                clothes.append(value)

    if body is None or body.filename == '':
        return jsonify({'error': 'No body provided'}), 400
    if not clothes:
        return jsonify({'error': 'No clothes provided'}), 400

    if not _is_allowed_image(body):
        return jsonify({'error': 'Invalid file type'}), 400
    for c in clothes:
        if not _is_allowed_image(c):
            return jsonify({'error': 'Invalid file type'}), 400

    tmp = tempfile.NamedTemporaryFile(delete=False)
    temp_path = tmp.name
    tmp.close()
    body.save(temp_path)

    try:
        parts = cloth_segmenter.parse(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    part_names = ", ".join(parts.keys()) if parts else "unknown parts"
    clothing_names = ", ".join(os.path.splitext(c.filename)[0] for c in clothes)
    prompt = (
        f"Combine body parts {part_names} with clothing items: {clothing_names}"
    )
    try:
        chat = _call_openai_with_retry(
            openai.ChatCompletion.create,
            messages=[{"role": "user", "content": prompt}],
            model="gpt-3.5-turbo",
        )
        suggestion_text = chat["choices"][0]["message"]["content"]
        image = _call_openai_with_retry(openai.Image.create, prompt=prompt)
        image_url = image["data"][0]["url"]
    except openai.error.OpenAIError:
        logger.exception("OpenAI request failed")
        return jsonify({"error": "OpenAI request failed"}), 502

    return jsonify({'suggestions': [suggestion_text], 'composite_url': image_url})


@app.route('/register/email', methods=['POST'])
def register_email():
    email = request.form.get('email')
    password = request.form.get('password')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    hashed = generate_password_hash(password)
    with SessionLocal() as session:
        if session.query(User).filter_by(identifier=email).first():
            return jsonify({'error': 'User already exists'}), 409
        session.add(User(identifier=email, method='email', password=hashed))
        session.commit()
    return jsonify({'message': f'Registered {email} via email'})


@app.route('/register/phone', methods=['POST'])
def register_phone():
    phone = request.form.get('phone')
    if not phone:
        return jsonify({'error': 'Phone number required'}), 400
    with SessionLocal() as session:
        if session.query(User).filter_by(identifier=phone).first():
            return jsonify({'error': 'User already exists'}), 409
        session.add(User(identifier=phone, method='phone'))
        session.commit()
    return jsonify({'message': f'Registered {phone} via phone'})


@app.route('/register/google', methods=['POST'])
def register_google():
    token = request.form.get('token')
    if not token:
        return jsonify({'error': 'Google token required'}), 400
    with SessionLocal() as session:
        if session.query(User).filter_by(identifier=token).first():
            return jsonify({'error': 'User already exists'}), 409
        session.add(User(identifier=token, method='google'))
        session.commit()
    return jsonify({'message': 'Registered via Google'})


@app.route('/register/facebook', methods=['POST'])
def register_facebook():
    token = request.form.get('token')
    if not token:
        return jsonify({'error': 'Facebook token required'}), 400
    with SessionLocal() as session:
        if session.query(User).filter_by(identifier=token).first():
            return jsonify({'error': 'User already exists'}), 409
        session.add(User(identifier=token, method='facebook'))
        session.commit()
    return jsonify({'message': 'Registered via Facebook'})


@app.route('/get_user', methods=['POST'])
def get_user():
    """Return basic user info for testing purposes."""
    identifier = request.form.get('identifier')
    if not identifier:
        return jsonify({'error': 'identifier required'}), 400
    with SessionLocal() as session:
        user = session.query(User).filter_by(identifier=identifier).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'identifier': user.identifier, 'method': user.method})

if __name__ == '__main__':
    flag = os.getenv('FLASK_DEBUG')
    debug_mode = flag.lower() in {'1', 'true', 'yes'} if flag is not None else False
    app.run(debug=debug_mode)
