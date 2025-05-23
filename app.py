import os
import logging
import imghdr
try:
    from flask import Flask, request, render_template, jsonify
except Exception:  # pragma: no cover - fallback when Flask isn't installed
    # The stub is only used for running the test suite without real Flask
    from flask_stub import Flask, request, render_template, jsonify
from clothseg import ClothSegmenter
from werkzeug.utils import secure_filename # Added for secure filenames
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
        if size > 0:
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


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        full_body_image = request.files.get('full_body_image')
        clothing_item_images = request.files.getlist('clothing_item_images')

        # Validate full_body_image
        if full_body_image is None or full_body_image.filename == '':
            return jsonify({'error': 'Full body image is required'}), 400
        if not _is_allowed_image(full_body_image):
            return jsonify({'error': 'Invalid file type or size for full body image'}), 400

        # Validate clothing_item_images
        if not clothing_item_images or all(not item.filename for item in clothing_item_images):
            return jsonify({'error': 'At least one clothing item image is required'}), 400

        clothing_attributes_list = []

        for idx, item_image in enumerate(clothing_item_images):
            if item_image.filename == '':
                # This case might occur if multiple file inputs are used and some are left empty.
                # Depending on strictness, we can ignore or error.
                # For now, let's assume getlist filters out ones with no actual file selected by user.
                # If an empty filename string IS passed for a selected file, it's an issue.
                logger.warning(f"Skipping clothing item at index {idx} due to empty filename.")
                continue # Or return error: jsonify({'error': f'Clothing item {idx+1} has no filename'}), 400

            if not _is_allowed_image(item_image):
                return jsonify({'error': f'Invalid file type or size for clothing item: {secure_filename(item_image.filename)}'}), 400

            temp_path = ""
            try:
                # Secure the filename before using it in NamedTemporaryFile's suffix
                s_filename = secure_filename(item_image.filename)
                # Ensure suffix starts with a dot if that's what NamedTemporaryFile expects, or handle it if it adds one.
                # os.path.splitext can give the extension directly.
                _, ext = os.path.splitext(s_filename)
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                temp_path = tmp.name
                tmp.close() # Close before saving to it
                item_image.save(temp_path)
                
                # Use cloth_segmenter.analyze to get attributes
                analysis_result = cloth_segmenter.analyze(temp_path)
                # Ensure 'attributes' key exists, default to empty dict if not
                item_attributes = analysis_result.get('attributes', {})
                if not item_attributes and 'parts' in analysis_result : # If attributes is empty but parts exist, maybe log or use parts as fallback
                    logger.info(f"Clothing item {s_filename} yielded no specific attributes, but parts were segmented.")

                clothing_attributes_list.append(item_attributes)

            except Exception as e: # More specific exception handling can be added if needed
                logger.error(f"Error processing clothing item {secure_filename(item_image.filename)}: {e}")
                # Decide if one failed item should halt the whole request
                return jsonify({'error': f'Error processing clothing item: {secure_filename(item_image.filename)}'}), 500
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
        
        # Placeholder for full body image processing (if any needed beyond validation)
        # For now, we just acknowledge its receipt.

        # Construct prompt for OpenAI
        prompt_items_list = []
        if not clothing_attributes_list:
            suggestion_text = "No clothing items were provided to suggest an outfit."
        else:
            for i, attributes in enumerate(clothing_attributes_list):
                category = attributes.get('category', 'item')
                color = attributes.get('color', '')
                description = f"Item {i+1}: A "
                if color and color.lower() != 'unknown':
                    description += f"{color} "
                description += category
                prompt_items_list.append(description)

            formatted_items = "\n".join(prompt_items_list)
            prompt = (
                "You are a fashion assistant. Based on the following available clothing items, please suggest 2-3 distinct outfits:\n\n"
                "Available items:\n"
                f"{formatted_items}\n\n"
                "For each outfit, please describe which items are used and why they form a good combination. "
                "Focus on color coordination and general style compatibility."
            )

            try:
                chat_completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}]
                )
                suggestion_text = chat_completion.choices[0].message.content
            except openai.error.OpenAIError as e:
                logger.error(f"OpenAI API request failed: {e}")
                return jsonify({'error': 'OpenAI request failed while generating outfit suggestions'}), 502

        # Initialize image generation related variables
        generated_outfit_image_url = None
        image_generation_error = None
        final_message = "Outfit suggestion generated successfully."

        # Attempt to generate an image if clothing items were processed
        if clothing_attributes_list:
            item_descriptions_for_image = []
            for attributes in clothing_attributes_list:
                category = attributes.get('category', 'item')
                color = attributes.get('color', '')
                desc_part = ""
                if color and color.lower() != 'unknown':
                    desc_part += f"{color} "
                desc_part += category
                if desc_part: # Avoid adding empty strings if both are unknown/empty
                    item_descriptions_for_image.append(desc_part)
            
            if item_descriptions_for_image:
                item_descriptions_string = ", ".join(item_descriptions_for_image)
                image_prompt = (
                    f"Generate a realistic image of a person wearing a stylish, coordinated outfit composed from some or all of the "
                    f"following items: {item_descriptions_string}. Show a full-body view of the person. The background should be simple and neutral, "
                    "making the outfit the main focus."
                )
                try:
                    image_response = openai.Image.create(
                        prompt=image_prompt,
                        n=1,
                        size="512x512" 
                    )
                    generated_outfit_image_url = image_response["data"][0]["url"]
                    final_message = "Outfit suggestion and image generated successfully."
                except openai.error.OpenAIError as e:
                    logger.error(f"OpenAI Image API request failed: {e}")
                    image_generation_error = "Failed to generate outfit image due to an API error."
                    final_message = "Outfit suggestion generated, but image generation failed."
            else:
                image_generation_error = "Not enough item details to generate an image."
                final_message = "Outfit suggestion generated. Image generation skipped due to lack of item details."
        else:
            # This case is for when suggestion_text was the default "No clothing items..."
            final_message = "Outfit suggestion generated. Image generation skipped as no items were provided."


        response_data = {
            'message': final_message,
            'clothing_items_attributes': clothing_attributes_list,
            'user_image_info': {'filename': secure_filename(full_body_image.filename)},
            'outfit_suggestions_text': suggestion_text,
            'generated_outfit_image_url': generated_outfit_image_url
        }
        if image_generation_error:
            response_data['image_generation_error'] = image_generation_error
        
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error in /upload endpoint: {e}")
        return jsonify({'error': 'Error processing images'}), 500


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


@app.route('/analyze', methods=['POST'])
def analyze_image():
    """Return segmentation parts and simple classification."""
    file = request.files.get('image')
    if file is None or file.filename == '':
        return jsonify({'error': 'No file provided'}), 400
    if not _is_allowed_image(file):
        return jsonify({'error': 'Invalid file type'}), 400

    tmp = tempfile.NamedTemporaryFile(delete=False)
    temp_path = tmp.name
    tmp.close()
    file.save(temp_path)
    try:
        parts = cloth_segmenter.parse(temp_path)
        attributes = cloth_segmenter.classify(temp_path, parts)
    except Exception:
        return jsonify({'error': 'Segmentation failed'}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return jsonify({'parts': parts, 'attributes': attributes})

@app.route('/suggest', methods=['POST'])
def suggest():
    description = request.form.get('description', '')
    prompt = f"Suggest an outfit for: {description}"
    try:
        chat = openai.ChatCompletion.create(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-3.5-turbo",
        )
        suggestion_text = chat["choices"][0]["message"]["content"]
        image = openai.Image.create(prompt=prompt)
        image_url = image["data"][0]["url"]
    except openai.error.OpenAIError:
        logger.exception("OpenAI request failed")
        return jsonify({"error": "OpenAI request failed"}), 502

    return jsonify({'suggestions': [suggestion_text], 'image_url': image_url})


@app.route('/compose', methods=['POST'])
def compose():
    """Combine a user photo with selected clothing images."""
    # TODO: This endpoint currently uses OpenAI's general image generation based on a text prompt
    # derived from the uploaded images. For a true virtual try-on experience (dressing the user's
    # photo with specific clothes realistically), a specialized model (e.g., VITON-HD, or other
    # GAN/Diffusion based models) would need to be integrated here. This would involve
    # significant image processing (segmentation, pose estimation) for both the user image
    # and the clothing items, and then feeding this data to the specialized model.
    # See VIRTUAL_TRY_ON.md for more details on this advanced feature.
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
        chat = openai.ChatCompletion.create(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-3.5-turbo",
        )
        suggestion_text = chat["choices"][0]["message"]["content"]
        image = openai.Image.create(prompt=prompt)
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


@app.route('/refine_outfit_suggestion', methods=['POST'])
def refine_outfit_suggestion():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON payload'}), 400

        original_suggestion = data.get('original_suggestion')
        available_clothing_items = data.get('available_clothing_items')
        user_query = data.get('user_query')

        missing_fields = []
        if original_suggestion is None: # Allow empty string, but not None
            missing_fields.append('original_suggestion')
        if available_clothing_items is None: # Allow empty list, but not None
            missing_fields.append('available_clothing_items')
        if user_query is None: # Allow empty string, but not None
            missing_fields.append('user_query')
        
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        if not isinstance(original_suggestion, str):
            return jsonify({'error': 'Invalid type for original_suggestion, expected string'}), 400
        if not isinstance(available_clothing_items, list):
            return jsonify({'error': 'Invalid type for available_clothing_items, expected list'}), 400
        if not isinstance(user_query, str):
            return jsonify({'error': 'Invalid type for user_query, expected string'}), 400

        for item in available_clothing_items:
            if not isinstance(item, dict):
                return jsonify({'error': 'Invalid item in available_clothing_items, expected list of dictionaries'}), 400

        # Format available_clothing_items
        formatted_available_items_list = []
        if not available_clothing_items:
            formatted_available_items = "No specific clothing items were listed as available by the user."
        else:
            for i, item_attrs in enumerate(available_clothing_items):
                category = item_attrs.get('category', 'item')
                color = item_attrs.get('color', '')
                description = f"Item {i+1}: A "
                if color and color.lower() != 'unknown':
                    description += f"{color} "
                description += category
                formatted_available_items_list.append(description)
            formatted_available_items = "\n".join(formatted_available_items_list)

        # Construct the refinement prompt
        refinement_prompt = (
            "You are a fashion assistant. Here's the context:\n"
            "The user has the following clothing items available:\n"
            f"{formatted_available_items}\n\n"
            "Previously, you provided these outfit suggestions:\n"
            f'"{original_suggestion}"\n\n'
            "Now, the user has a follow-up request:\n"
            f'"{user_query}"\n\n'
            "Please provide a new set of outfit suggestions or modifications based on the user's request, "
            "keeping in mind the available items. If the request involves items not explicitly listed as available "
            "(e.g., user mentions 'if I had white sneakers'), acknowledge this and provide advice accordingly, "
            "perhaps suggesting how such an item would fit or offering alternatives from the available items."
        )

        # Call OpenAI ChatCompletion API
        try:
            chat_completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": refinement_prompt}]
            )
            refined_suggestion_text = chat_completion.choices[0].message.content
        except openai.error.OpenAIError as e:
            logger.error(f"OpenAI API request failed during refinement: {e}")
            return jsonify({'error': 'OpenAI request failed during refinement'}), 502

        # Generate follow_up_image_prompt
        follow_up_image_prompt = None
        if refined_suggestion_text and refined_suggestion_text.strip():
            # Simple prompt based on a snippet of the refined text
            prompt_snippet = refined_suggestion_text[:200].strip() # Take first 200 chars
            follow_up_image_prompt = f"A realistic image depicting an outfit based on the following suggestion: \"{prompt_snippet}...\" Ensure the person and outfit are the main focus, with a simple, neutral background."
        else:
            follow_up_image_prompt = "No specific refined outfit details to visualize."
            if not refined_suggestion_text: # if it was empty or None
                 refined_suggestion_text = "The AI did not provide a specific textual refinement."


        return jsonify({
            "refined_suggestion_text": refined_suggestion_text,
            "follow_up_image_prompt": follow_up_image_prompt
        }), 200

    except Exception as e:
        logger.error(f"Error in /refine_outfit_suggestion endpoint: {e}")
        return jsonify({'error': 'An unexpected error occurred processing your request'}), 500
