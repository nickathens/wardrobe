class ChatCompletion:
    @staticmethod
    def create(*, messages, model="gpt-3.5-turbo"):
        content = messages[-1]["content"] if messages else ""
        suggestion = f"AI suggestion based on {content}"
        return {"choices": [{"message": {"content": suggestion}}]}

class Image:
    @staticmethod
    def create(*, prompt, n=1, size="512x512"):
        url = f"https://example.com/{prompt.replace(' ', '_')}.png"
        return {"data": [{"url": url}]}

api_key = None
