import openai_stub


def test_chatcompletion_invalid_messages():
    try:
        openai_stub.ChatCompletion.create(messages=[])
    except openai_stub.error.OpenAIError:
        pass
    else:
        raise AssertionError("OpenAIError not raised")


def test_image_invalid_prompt():
    try:
        openai_stub.Image.create(prompt="")
    except openai_stub.error.OpenAIError:
        pass
    else:
        raise AssertionError("OpenAIError not raised")
