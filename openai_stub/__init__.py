class ChatCompletion:
    """Simplified stand-in for ``openai.ChatCompletion``.

    The stub validates basic input and raises ``OpenAIError`` on invalid
    arguments to better mimic the real client.
    """

    @staticmethod
    def create(*, messages, model="gpt-3.5-turbo"):
        """Return a deterministic response based on the last user message."""

        if not messages or "content" not in messages[-1] or not messages[-1]["content"]:
            raise error.OpenAIError("Invalid messages")

        content = messages[-1]["content"]
        suggestion = f"AI suggestion based on {content}"
        return {"choices": [{"message": {"content": suggestion}}]}

class Image:
    """Simplified stand-in for ``openai.Image`` that validates input."""

    @staticmethod
    def create(*, prompt, n=1, size="512x512"):
        if not prompt:
            raise error.OpenAIError("Prompt required")

        url = f"https://example.com/{prompt.replace(' ', '_')}.png"
        return {"data": [{"url": url}]}

class error:
    class OpenAIError(Exception):
        """Exception raised for OpenAI API errors in the stub."""
        pass

api_key = None
