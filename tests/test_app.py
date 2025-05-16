import io
import os
from types import SimpleNamespace
import pytest

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def monkeypatch():
    patches = []

    class MP:
        def setattr(self, target, name, value):
            original = getattr(target, name)
            patches.append((target, name, original))
            setattr(target, name, value)

    mp = MP()
    yield mp
    for target, name, original in reversed(patches):
        setattr(target, name, original)

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200

def test_upload_route(client):
    data = {
        'image': (io.BytesIO(b'mock image data'), 'test.png')
    }
    response = client.post(
        '/upload',
        data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {'suggestions': ['Outfit suggestion based on test.png']}

def test_upload_route_no_file(client):
    response = client.post(
        '/upload',
        data={},
        content_type='multipart/form-data'
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload == {'error': 'No file provided'}


def test_parse_route(client):
    data = {
        'image': (io.BytesIO(b'mock image data'), 'test.png')
    }
    response = client.post(
        '/parse',
        data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert 'parts' in payload

def test_suggest_route(client, monkeypatch):
    os.environ['OPENAI_API_KEY'] = 'testkey'
    import openai
    openai.api_key = 'testkey'

    def fake_create(model, messages):
        content = 'Option A\nOption B'
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

    monkeypatch.setattr(openai.ChatCompletion, 'create', fake_create)

    data = {'description': 'casual outfit'}
    response = client.post('/suggest', data=data)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {'suggestions': ['Option A', 'Option B']}


def test_register_email(client):
    data = {'email': 'user@example.com', 'password': 'secret'}
    response = client.post('/register/email', data=data)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {'message': 'Registered user@example.com via email'}


def test_register_phone_missing_number(client):
    response = client.post('/register/phone', data={})
    assert response.status_code == 400
    payload = response.get_json()
    assert payload == {'error': 'Phone number required'}


def test_generate_route(client, monkeypatch):
    class MockResp:
        def __init__(self):
            self.content = b'img'
            self.status_code = 200
            self.headers = {'Content-Type': 'image/png'}

        def raise_for_status(self):
            pass

    def fake_post(url, files=None, data=None):
        return MockResp()

    import requests
    monkeypatch.setattr(requests, 'post', fake_post)

    data = {
        'parts': '{}',
        'photo': (io.BytesIO(b'body'), 'body.png'),
    }
    resp = client.post('/generate', data=data, content_type='multipart/form-data')
    assert resp.status_code == 200
    assert resp.data == b'img'
