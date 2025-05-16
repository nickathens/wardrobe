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

def test_suggest_route(client):
    data = {'description': 'casual outfit'}
    response = client.post('/suggest', data=data)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {'suggestions': ['Outfit suggestion for: casual outfit']}


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
