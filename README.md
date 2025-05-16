# wardrobe

To run the app, define the `OPENAI_API_KEY` environment variable.
You can create a `.env` file in the project root with the following content:

```bash
OPENAI_API_KEY=your-openai-api-key
```

Before running `app.py`, load the variables:

```bash
export $(cat .env | xargs)
python app.py
```
