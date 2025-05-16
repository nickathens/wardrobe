# Wardrobe

This project provides a simple Flask application that allows users to upload an image or provide a text description to receive outfit suggestions.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the development server:

```bash
python app.py
```

Then visit `http://localhost:5000` in your browser.

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
