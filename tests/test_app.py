import io
import pytest

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
    response = client.post(
        '/upload',
        data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {'suggestions': ['Outfit suggestion based on test.png']}

def test_upload_no_file_returns_400(client):
    response = client.post('/upload', data={}, content_type='multipart/form-data')
    assert response.status_code == 400
    payload = response.get_json()
    assert payload == {'error': 'No file provided'}

def test_suggest_route(client):
    data = {'description': 'casual outfit'}
    response = client.post('/suggest', data=data)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {'suggestions': ['Outfit suggestion for: casual outfit']}

def test_suggest_special_characters(client):
    data = {'description': '<script>alert("x")</script>'}
    response = client.post('/suggest', data=data)
    assert response.status_code == 200
    payload = response.get_json()
    assert '<script>' not in payload['suggestions'][0]
    assert '&lt;script&gt;' in payload['suggestions'][0]
