# Wardrobe

This project provides a simple Flask application that allows users to upload an image or provide a text description to receive outfit suggestions.

The repository now integrates a U^2-Net based cloth segmentation model. When the
pre-trained weights are available, real segmentation masks are produced for
images sent to the `/parse` endpoint. If the weights are missing, the parser
falls back to dummy data so the rest of the application continues to work.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

### Environment variables

The application uses the `openai` package to generate suggestions and images.
Set the following variable before running the server:

- `OPENAI_API_KEY` - your OpenAI API key

Run the development server. Set `FLASK_DEBUG=1` to enable debug mode:

```bash
FLASK_DEBUG=1 python app.py
```

If `FLASK_DEBUG` is unset or evaluates to false, the server runs without debug
enabled.

Then visit `http://localhost:5000` in your browser.

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

## Registration

Users can register using one of several methods:

- **Email**: `POST /register/email` with `email` and `password` form fields.
- **Phone**: `POST /register/phone` with `phone` form field.
- **Google**: `POST /register/google` with an OAuth `token`.
- **Facebook**: `POST /register/facebook` with an OAuth `token`.

The application stores registration data in memory for demonstration
purposes only.

## Running Tests

Execute the test suite using `pytest`:

```bash
pytest
```

## License

This project is licensed under the [MIT License](LICENSE).
