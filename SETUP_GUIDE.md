# Setup Guide: Enabling Full Application Functionality

## Introduction

This guide provides step-by-step instructions to set up and run this application with all its features enabled, including AI-powered functionalities and accurate cloth segmentation. Following these steps will ensure you are using the real libraries and not the placeholder stubs.

## Prerequisites

Before you begin, ensure you have the following:

*   **Python 3.x installed:** You can download it from [python.org](https://www.python.org/downloads/).
*   **Access to a terminal or command prompt:** This will be used for running commands.

## Installation

1.  **Clone the Repository (if you haven't already):**
    If you're working with a fresh copy or setting this up in a new environment, you'd typically clone the repository. However, as you're likely already viewing this within the project, you can skip this step.
    ```bash
    # git clone <repository-url>
    # cd <repository-name>
    ```

2.  **Set Up a Virtual Environment (Recommended):**
    Using a virtual environment keeps your project dependencies isolated.
    ```bash
    python -m venv venv
    ```
    Activate it:
    *   On Windows: `venv\Scripts\activate`
    *   On macOS and Linux: `source venv/bin/activate`

3.  **Install Python Dependencies:**
    This project uses a `requirements.txt` file to manage its dependencies. Install them using pip:
    ```bash
    pip install -r requirements.txt
    ```
    **Important:** This command installs the *real* versions of libraries like Flask, OpenAI, SQLAlchemy, etc., which are necessary for full functionality.

## Configuration

To unlock the application's advanced features, you need to configure a few things:

### 1. OpenAI API Key

The application uses the OpenAI API for its AI-powered features.

*   **Obtain an OpenAI API Key:**
    1.  Go to [platform.openai.com/signup](https://platform.openai.com/signup) to create an account or log in.
    2.  Navigate to the [API keys section](https://platform.openai.com/account/api-keys).
    3.  Create a new secret key and copy it immediately. You won't be able to see it again.

*   **Set the `OPENAI_API_KEY` Environment Variable:**
    The application expects the API key to be available as an environment variable named `OPENAI_API_KEY`.
    *   **macOS/Linux:**
        ```bash
        export OPENAI_API_KEY='your_api_key_here'
        ```
        To make this permanent, add the line to your shell's configuration file (e.g., `~/.bashrc`, `~/.zshrc`) and then source it (e.g., `source ~/.bashrc`).
    *   **Windows (Command Prompt):**
        ```bash
        set OPENAI_API_KEY=your_api_key_here
        ```
    *   **Windows (PowerShell):**
        ```bash
        $env:OPENAI_API_KEY="your_api_key_here"
        ```
        For permanent storage on Windows, search for "environment variables" in the system settings.

    **Crucial:** Without this key, AI features will not work, and you might encounter errors or see stubbed responses.

### 2. Cloth Segmentation Model (U^2-Net)

For accurate clothing segmentation in images, the application uses `clothseg.py`, which leverages the U^2-Net pre-trained model.

*   **Download the Model:**
    The `u2net.pth` model file (approximately 176MB) needs to be downloaded. You can do this by running the `clothseg.py` script with a special command:
    ```bash
    python clothseg.py --download-model
    ```
    This command will download the model to the default location: `~/.u2net/u2net.pth` (i.e., a `.u2net` directory in your user's home directory).

*   **Automatic Usage:**
    The `ClothSegmenter` class in `clothseg.py` is designed to automatically look for `u2net.pth` in the default path (`~/.u2net/u2net.pth`). If the model is found there, it will be loaded and used. You can also specify a custom path to the model if needed when instantiating `ClothSegmenter`.

## Ensuring Real Libraries are Used (Crucial)

As mentioned in the `README.md`, this repository includes stub modules (`flask_stub/`, `openai_stub/`, `sqlalchemy_stub/`, `werkzeug_stub/`) to allow basic exploration without installing all dependencies or setting up API keys. **For full functionality, these stubs MUST NOT be used.**

To ensure the real libraries (installed via `pip install -r requirements.txt`) are used:

*   **Option 1: Remove the Stub Directories (Recommended):**
    This is the cleanest way to ensure the stubs don't interfere. Delete the following directories from your project's root:
    *   `flask_stub/`
    *   `openai_stub/`
    *   `sqlalchemy_stub/`
    *   `werkzeug_stub/`

*   **Option 2: Run from an External Directory (If stubs must be kept):**
    If you have a specific reason to keep the stub directories in your project, you must ensure that Python does not find them when looking for modules. The easiest way to do this is to run the application from a directory *outside* the project's root. Python's module search path (`PYTHONPATH`) typically includes the current working directory first. If you run `python app.py` from within the project root, it might pick up `openai_stub` instead of the real `openai` library.

    **We strongly recommend removing the stub directories for any development or production setup to avoid confusion.**

## Database Setup

The application uses SQLAlchemy for database interactions.

*   By default, it uses an in-memory SQLite database (`sqlite:///:memory:`). This is often sufficient for development and testing, as the database is created anew each time the application starts.
*   You can specify a different database by setting the `DATABASE_URL` environment variable (e.g., `export DATABASE_URL='postgresql://user:password@host:port/dbname'`).

For standard setup and testing the full features, the default in-memory database is fine.

## Running the Application

Once all dependencies are installed, configurations are set, and you've ensured stubs won't interfere:

1.  **Ensure your virtual environment is active.**
2.  **Set `FLASK_DEBUG=1` for development mode (provides helpful debugging information):**
    ```bash
    export FLASK_DEBUG=1 # macOS/Linux
    # set FLASK_DEBUG=1   # Windows Command Prompt
    # $env:FLASK_DEBUG="1" # Windows PowerShell
    ```
3.  **Run the application:**
    ```bash
    python app.py
    ```
4.  **Access the application:**
    Open your web browser and go to `http://localhost:5000`.

## Troubleshooting (Brief)

*   **"OpenAI API key not set" / AI features not working:**
    *   Double-check that you have correctly set the `OPENAI_API_KEY` environment variable.
    *   Ensure the key itself is valid and has API access on the OpenAI platform.
    *   Restart your terminal or command prompt session after setting the variable to ensure it's loaded.

*   **"Cloth segmentation is coarse" / Background removal is poor:**
    *   Ensure you have downloaded the `u2net.pth` model using `python clothseg.py --download-model`.
    *   Verify the model is in the expected location (`~/.u2net/u2net.pth`) or that `clothseg.py` is correctly configured if using a custom path.

*   **"Still seeing stub behavior" / Application seems limited:**
    *   You are likely still using the stub modules. **Strongly ensure you have removed the `flask_stub/`, `openai_stub/`, `sqlalchemy_stub/`, and `werkzeug_stub/` directories.**
    *   If you opted not to remove them, make sure you are running `python app.py` from a directory *outside* the project's root.

By following this guide, you should have a fully functional instance of the application running.
