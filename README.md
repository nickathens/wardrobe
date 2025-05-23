# Wardrobe

This project provides a simple Flask application that allows users to upload an image or provide a text description to receive outfit suggestions.

The `templates/index.html` page links to a small stylesheet under `static/styles.css` for basic layout and uses JavaScript to display the generated image returned by the API.

The repository now integrates a U^2-Net based cloth segmentation model. When the
pre-trained weights are available, real segmentation masks are produced for
images sent to the `/parse` endpoint. If the weights are missing, the parser
computes a very coarse split of the image to approximate upper and lower body
regions so the rest of the application continues to work.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

### Stub modules

The repository bundles lightweight replacements for `flask`, `werkzeug`,
`openai`, and `pytest` under the names `flask_stub`, `werkzeug_stub`,
`openai_stub`, and a minimal `pytest` package. These stubs exist solely so the
test suite can run in environments without network access. For any real usage
you must install the genuine packages with `pip install -r requirements.txt`.
Once the real packages are installed, remove the stub directories (or run the
application from outside the repository) so that ``PYTHONPATH`` does not pick up
the stubs.

### Environment variables

The application uses the `openai` package to generate suggestions and images.
Set the following variable before running the server:

- `OPENAI_API_KEY` - your OpenAI API key

If the real `openai` package is installed and this variable is not set, the
server will exit on startup.

Run the development server. Set `FLASK_DEBUG=1` to enable debug mode:

```bash
FLASK_DEBUG=1 python app.py
```

If `FLASK_DEBUG` is unset or evaluates to false, the server runs without debug
enabled.

Then visit `http://localhost:5000` in your browser.

### OpenAI API usage

When the real `openai` package is installed, the application communicates
directly with OpenAI's API to generate text and images. Any prompts or other
data you send will therefore be transmitted to a third-party service
(OpenAI) for processing.

For local tests the repository bundles an `openai_stub` module that mimics the
API without making network calls.  The stub now performs basic validation and
raises a custom `OpenAIError` when invalid input is provided so tests can cover
error conditions.  Replace it with the genuine `openai` package in production so
the application can contact OpenAI's servers.

## Cloth Segmentation Model

Real cloth parsing relies on a pre-trained U^2-Net model. Download the weights
from [the official repository](https://github.com/xuebinqin/U-2-Net/releases/download/v1.0/u2net.pth)
(about 176&nbsp;MB) and place the file at `~/.u2net/u2net.pth` or specify the
path when instantiating :class:`clothseg.ClothSegmenter`.

You can download the weights from the command line:

```bash
python clothseg.py --download-model
```

This will store the model in `~/.u2net/u2net.pth` by default.

When the heavy U^2-Net weights are not available the application falls back to
OpenCV's GrabCut algorithm to roughly separate the foreground garment from the
background. The `/analyze` endpoint exposes this functionality and additionally
provides a lightweight classification that labels the item as a shirt, pants or
dress and estimates a basic colour.

## Advanced Features

### Virtual Try-On

The application currently uses general AI image generation (via OpenAI's DALL-E) for visual compositions in endpoints like `/compose`. This means it generates new images based on textual descriptions derived from uploaded items rather than performing a true virtual try-on.

A true virtual try-on system would involve overlaying specific garment images onto a user's photo, preserving their pose and body shape while realistically draping the clothes. This is a complex R&D task requiring specialized machine learning models. For more details on how such a system could be conceptualized and integrated, please see the [Virtual Try-On Implementation Guide](./VIRTUAL_TRY_ON.md). The existing `/compose` endpoint is a starting point for such an integration.

### Outfit Scoring with GPT-4

The application uses OpenAI's chat completions API to generate outfit suggestions. By default it calls the `gpt-3.5-turbo` model, but you can switch to GPT-4 by setting the `model` parameter in `app.py` to `gpt-4`. GPT-4 can reason about style compatibility using textual metadata for each garment, serving as a lighter alternative to specialised transformer models.


## Registration

Users can register using one of several methods:

- **Email**: `POST /register/email` with `email` and `password` form fields.
- **Phone**: `POST /register/phone` with `phone` form field.
- **Google**: `POST /register/google` with an OAuth `token`.
- **Facebook**: `POST /register/facebook` with an OAuth `token`.

Registration information is now persisted using a small SQLite database
through SQLAlchemy. While convenient for local testing, this setup is
still simplified and not intended for production authentication needs.

## Running Tests

Execute the test suite using `pytest`:

```bash
pytest
```

## License

This project is licensed under the [MIT License](LICENSE).
