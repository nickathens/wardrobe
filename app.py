import os


def main():
    api_key = os.environ["OPENAI_API_KEY"]
    print(f"Loaded API key of length {len(api_key)}")


if __name__ == "__main__":
    main()
