import io
import os
import pytest
from unittest.mock import patch

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200

def test_upload_route(client):
    data = {
        'image': (io.BytesIO(b'mock image data'), 'test.png')
    }
    with patch('app.openai.ChatCompletion.create') as chat_create, \
         patch('app.openai.Image.create') as img_create:
        chat_create.return_value = {
            'choices': [{'message': {'content': 'Stub suggestion'}}]
        }
        img_create.return_value = {
            'data': [{'url': 'http://example.com/outfit.png'}]
        }
        response = client.post(
            '/upload',
            data=data,
            content_type='multipart/form-data'
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {
        'suggestions': ['Stub suggestion'],
        'image_url': 'http://example.com/outfit.png'
    }

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

def test_parse_route_no_file(client):
    response = client.post(
        '/parse',
        data={},
        content_type='multipart/form-data'
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload == {'error': 'No file provided'}

def test_suggest_route(client):
    data = {'description': 'casual outfit'}
    with patch('app.openai.ChatCompletion.create') as chat_create, \
         patch('app.openai.Image.create') as img_create:
        chat_create.return_value = {
            'choices': [{'message': {'content': 'Stub suggest desc'}}]
        }
        img_create.return_value = {
            'data': [{'url': 'http://example.com/desc.png'}]
        }
        response = client.post('/suggest', data=data)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {
        'suggestions': ['Stub suggest desc'],
        'image_url': 'http://example.com/desc.png'
    }


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


def test_parse_cleanup_on_failure(client):
    temp_path = os.path.join('/tmp', 'fail.png')

    if os.path.exists(temp_path):
        os.remove(temp_path)

    def fail_parse(path):
        raise RuntimeError('boom')

    data = {
        'image': (io.BytesIO(b'mock image data'), 'fail.png')
    }

    class DummyTmp:
        def __init__(self, name):
            self.name = name
        def close(self):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass

    def dummy_tmp(*args, **kwargs):
        return DummyTmp(temp_path)

    with patch('app.tempfile.NamedTemporaryFile', side_effect=dummy_tmp), \
         patch('app.cloth_segmenter.parse', side_effect=fail_parse):
        try:
            client.post(
                '/parse',
                data=data,
                content_type='multipart/form-data'
            )
        except RuntimeError:
            pass
    assert not os.path.exists(temp_path)
