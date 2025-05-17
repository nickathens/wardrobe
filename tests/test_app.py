import io
import os
import base64
import types
import contextlib
import pytest
from unittest.mock import patch
from flask_stub import File

from app import app
import app as app_module

PNG_BYTES = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQImWNgYAAAAAUAAarVyFEAAAAASUVORK5CYII='
)

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
        'image': (io.BytesIO(PNG_BYTES), 'test.png')
    }
    with patch.object(app_module.cloth_segmenter, 'parse') as parse, \
         patch('app.openai.ChatCompletion.create') as chat_create, \
         patch('app.openai.Image.create') as img_create:
        parse.return_value = {
            'upper_body': [],
            'lower_body': [],
            'full_body': []
        }
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
        parse.assert_called_once()
        chat_create.assert_called_once_with(
            messages=[{"role": "user", "content": "Suggest an outfit based on the clothing parts: upper_body, lower_body, full_body"}],
            model="gpt-3.5-turbo",
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


def test_upload_route_invalid_file_type(client):
    data = {
        'image': (io.BytesIO(b'not an image'), 'test.txt')
    }
    response = client.post(
        '/upload',
        data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Invalid file type'}


def test_upload_route_invalid_image_content(client):
    data = {
        'image': (io.BytesIO(b'not really an image'), 'fake.png')
    }
    response = client.post(
        '/upload',
        data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Invalid file type'}


def test_upload_route_large_file(client):
    big = io.BytesIO(b'x' * (3 * 1024 * 1024))
    data = {
        'image': (big, 'big.png')
    }
    response = client.post(
        '/upload',
        data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Invalid file type'}


def test_upload_route_openai_error(client):
    data = {
        'image': (io.BytesIO(PNG_BYTES), 'test.png')
    }
    with patch.object(app_module.cloth_segmenter, 'parse') as parse, \
         patch('app.openai.ChatCompletion.create', side_effect=app_module.openai.error.OpenAIError('fail')) as chat_create, \
         patch('app.openai.Image.create') as img_create:
        parse.return_value = {
            'upper_body': [],
            'lower_body': [],
            'full_body': []
        }
        response = client.post(
            '/upload',
            data=data,
            content_type='multipart/form-data'
        )
        chat_create.assert_called_once()
        img_create.assert_not_called()
    assert response.status_code == 502
    assert response.get_json() == {'error': 'OpenAI request failed'}


def test_parse_route(client):
    data = {
        'image': (io.BytesIO(PNG_BYTES), 'test.png')
    }
    response = client.post(
        '/parse',
        data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {
        'parts': {
            'upper_body': [[0, 0, 1, 0]],
            'lower_body': [[0, 0, 1, 1]],
            'full_body': [[0, 0, 1, 1]],
        }
    }

def test_parse_route_no_file(client):
    response = client.post(
        '/parse',
        data={},
        content_type='multipart/form-data'
    )
    assert response.status_code == 400
    payload = response.get_json()
    assert payload == {'error': 'No file provided'}


def test_parse_route_invalid_file_type(client):
    data = {
        'image': (io.BytesIO(b'not an image'), 'test.txt')
    }
    response = client.post(
        '/parse',
        data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Invalid file type'}

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
        chat_create.assert_called_once_with(
            messages=[{"role": "user", "content": "Suggest an outfit for: casual outfit"}],
            model="gpt-3.5-turbo",
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {
        'suggestions': ['Stub suggest desc'],
        'image_url': 'http://example.com/desc.png'
    }


def test_suggest_route_openai_error(client):
    data = {'description': 'casual outfit'}
    with patch('app.openai.ChatCompletion.create', side_effect=app_module.openai.error.OpenAIError('fail')) as chat_create, \
         patch('app.openai.Image.create') as img_create:
        response = client.post('/suggest', data=data)
        chat_create.assert_called_once()
        img_create.assert_not_called()
    assert response.status_code == 502
    assert response.get_json() == {'error': 'OpenAI request failed'}


def test_compose_route(client):
    data = {
        'body': (io.BytesIO(PNG_BYTES), 'body.png'),
        'clothes1': (io.BytesIO(PNG_BYTES), 'shirt.png'),
        'clothes2': (io.BytesIO(PNG_BYTES), 'pants.jpg'),
    }
    with patch.object(app_module.cloth_segmenter, 'parse') as parse, \
         patch('app.openai.ChatCompletion.create') as chat_create, \
         patch('app.openai.Image.create') as img_create:
        parse.return_value = {
            'upper_body': [],
            'lower_body': [],
            'full_body': []
        }
        chat_create.return_value = {
            'choices': [{'message': {'content': 'combo'}}]
        }
        img_create.return_value = {
            'data': [{'url': 'http://example.com/combo.png'}]
        }
        response = client.post(
            '/compose',
            data=data,
            content_type='multipart/form-data'
        )
        parse.assert_called_once()
        chat_create.assert_called_once_with(
            messages=[{'role': 'user', 'content':
                       'Combine body parts upper_body, lower_body, full_body with clothing items: shirt, pants'}],
            model='gpt-3.5-turbo',
        )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {
        'suggestions': ['combo'],
        'composite_url': 'http://example.com/combo.png'
    }


def test_compose_route_missing_body(client):
    data = {
        'clothes1': (io.BytesIO(PNG_BYTES), 'shirt.png')
    }
    response = client.post('/compose', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.get_json() == {'error': 'No body provided'}


def test_compose_route_no_clothes(client):
    data = {
        'body': (io.BytesIO(PNG_BYTES), 'body.png')
    }
    response = client.post('/compose', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.get_json() == {'error': 'No clothes provided'}


def test_compose_route_invalid_file_type(client):
    data = {
        'body': (io.BytesIO(PNG_BYTES), 'body.txt'),
        'clothes1': (io.BytesIO(PNG_BYTES), 'shirt.png')
    }
    response = client.post('/compose', data=data, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Invalid file type'}


def test_compose_route_openai_error(client):
    data = {
        'body': (io.BytesIO(PNG_BYTES), 'body.png'),
        'clothes1': (io.BytesIO(PNG_BYTES), 'shirt.png')
    }
    with patch.object(app_module.cloth_segmenter, 'parse') as parse, \
         patch('app.openai.ChatCompletion.create', side_effect=app_module.openai.error.OpenAIError('fail')) as chat_create, \
         patch('app.openai.Image.create') as img_create:
        parse.return_value = {
            'upper_body': [],
            'lower_body': [],
            'full_body': []
        }
        response = client.post('/compose', data=data, content_type='multipart/form-data')
        chat_create.assert_called_once()
        img_create.assert_not_called()
    assert response.status_code == 502
    assert response.get_json() == {'error': 'OpenAI request failed'}


def test_register_email(client):
    data = {'email': 'user@example.com', 'password': 'secret'}
    response = client.post('/register/email', data=data)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {'message': 'Registered user@example.com via email'}

    # Verify the user was stored with a hashed password
    with app_module.SessionLocal() as session:
        user = session.query(app_module.User).filter_by(
            identifier='user@example.com'
        ).first()
        assert user is not None
        assert user.password != 'secret'
        assert app_module.check_password_hash(user.password, 'secret')

    # Verify the user can be retrieved in a new request
    response = client.post('/get_user', data={'identifier': 'user@example.com'})
    assert response.status_code == 200
    assert response.get_json() == {
        'identifier': 'user@example.com',
        'method': 'email'
    }


def test_register_phone_missing_number(client):
    response = client.post('/register/phone', data={})
    assert response.status_code == 400
    payload = response.get_json()
    assert payload == {'error': 'Phone number required'}


def test_register_phone_persists(client):
    data = {'phone': '1234567890'}
    response = client.post('/register/phone', data=data)
    assert response.status_code == 200
    assert response.get_json() == {
        'message': 'Registered 1234567890 via phone'
    }
    response = client.post('/get_user', data={'identifier': '1234567890'})
    assert response.status_code == 200
    assert response.get_json() == {
        'identifier': '1234567890',
        'method': 'phone'
    }


def test_register_email_duplicate(client):
    data = {'email': 'dup@example.com', 'password': 'pw'}
    first = client.post('/register/email', data=data)
    assert first.status_code == 200
    second = client.post('/register/email', data=data)
    assert second.status_code == 409


def test_register_phone_duplicate(client):
    data = {'phone': '5552223333'}
    first = client.post('/register/phone', data=data)
    assert first.status_code == 200
    second = client.post('/register/phone', data=data)
    assert second.status_code == 409


def test_register_google_duplicate(client):
    data = {'token': 'tok123'}
    first = client.post('/register/google', data=data)
    assert first.status_code == 200
    second = client.post('/register/google', data=data)
    assert second.status_code == 409


def test_register_facebook_duplicate(client):
    data = {'token': 'fb123'}
    first = client.post('/register/facebook', data=data)
    assert first.status_code == 200
    second = client.post('/register/facebook', data=data)
    assert second.status_code == 409


def test_parse_cleanup_on_failure(client):
    temp_path = os.path.join('/tmp', 'fail.png')

    if os.path.exists(temp_path):
        os.remove(temp_path)

    def fail_parse(path):
        raise RuntimeError('boom')

    data = {
        'image': (io.BytesIO(PNG_BYTES), 'fail.png')
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

    with patch.object(app_module.tempfile, 'NamedTemporaryFile', side_effect=dummy_tmp), \
         patch.object(app_module.cloth_segmenter, 'parse', side_effect=fail_parse):
        response = client.post(
            '/parse',
            data=data,
            content_type='multipart/form-data'
        )
    assert response.status_code == 500
    assert response.get_json() == {'error': 'Segmentation failed'}
    assert not os.path.exists(temp_path)


def test_parse_route_mask_keys(client):
    data = {
        'image': (io.BytesIO(PNG_BYTES), 'mask.png')
    }
    response = client.post(
        '/parse',
        data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert set(payload.get('parts', {}).keys()) == {'upper_body', 'lower_body', 'full_body'}


def test_analyze_route(client):
    data = {
        'image': (io.BytesIO(PNG_BYTES), 'mask.png')
    }
    with patch.object(app_module.cloth_segmenter, 'parse') as parse, \
         patch.object(app_module.cloth_segmenter, 'classify') as classify:
        parse.return_value = {
            'upper_body': [],
            'lower_body': [],
            'full_body': []
        }
        classify.return_value = {'category': 'shirt', 'color': 'red'}
        response = client.post('/analyze', data=data, content_type='multipart/form-data')
    assert response.status_code == 200
    assert response.get_json() == {
        'parts': {
            'upper_body': [],
            'lower_body': [],
            'full_body': []
        },
        'attributes': {'category': 'shirt', 'color': 'red'}
    }


def test_register_email_missing_fields(client):
    response = client.post('/register/email', data={})
    assert response.status_code == 400
    payload = response.get_json()
    assert payload == {'error': 'Email and password required'}


def test_register_google_missing_token(client):
    response = client.post('/register/google', data={})
    assert response.status_code == 400
    payload = response.get_json()
    assert payload == {'error': 'Google token required'}


def test_register_facebook_missing_token(client):
    response = client.post('/register/facebook', data={})
    assert response.status_code == 400
    payload = response.get_json()
    assert payload == {'error': 'Facebook token required'}


def test_no_api_key_with_stub():
    import importlib, os, sys
    os.environ.pop('OPENAI_API_KEY', None)
    sys.modules.pop('app', None)
    sys.modules.pop('openai', None)
    module = importlib.import_module('app')
    assert module.openai.__name__ == 'openai_stub'


def test_missing_api_key_real_openai():
    import importlib, os, sys, types
    os.environ.pop('OPENAI_API_KEY', None)
    dummy = types.SimpleNamespace(
        __name__='openai',
        ChatCompletion=types.SimpleNamespace(create=lambda *a, **k: None),
        Image=types.SimpleNamespace(create=lambda *a, **k: None),
        api_key=None,
    )
    sys.modules['openai'] = dummy
    sys.modules.pop('app', None)
    try:
        raised = False
        try:
            importlib.import_module('app')
        except RuntimeError:
            raised = True
        assert raised
    finally:
        sys.modules.pop('openai', None)
        sys.modules.pop('app', None)
        importlib.import_module('app')


def test_real_parser_with_weights():
    from clothseg import ClothSegmenter

    class DummyArray:
        def __init__(self, arr):
            self.arr = arr

        def tolist(self):
            return self.arr

    class DummyTensor:
        def __init__(self, arr):
            self.array = arr

        def float(self):
            return self

        def permute(self, *axes):
            return self

        def unsqueeze(self, dim):
            return self

        def __truediv__(self, val):
            return self

        def __gt__(self, val):
            def convert(a):
                if isinstance(a, list):
                    return [convert(x) for x in a]
                return 1 if a > val else 0
            return DummyTensor(convert(self.array))

        def __getitem__(self, item):
            return DummyTensor(self.array[item])

        def squeeze(self):
            return self

        def cpu(self):
            return self

        def numpy(self):
            return DummyArray(self.array)

    class DummyModel:
        def __call__(self, tensor):
            h = len(tensor.array)
            w = len(tensor.array[0]) if h else 0
            ones = [[[1 for _ in range(w)] for _ in range(h)] for _ in range(3)]
            return DummyTensor([ones])

        def eval(self):
            pass

    class DummyTorch:
        def __init__(self):
            self.jit = types.SimpleNamespace(load=lambda path: DummyModel())

        def from_numpy(self, arr):
            return DummyTensor(arr)

        def no_grad(self):
            return contextlib.nullcontext()

    class DummyImage:
        def open(self, path):
            class Img:
                def convert(self, mode):
                    return self
            return Img()

    class DummyNP:
        def array(self, img):
            return [[[0]]]

    img_path = os.path.join(os.path.dirname(__file__), 'small.png')
    with patch('clothseg.torch', DummyTorch(), create=True), \
         patch('clothseg.Image', DummyImage(), create=True), \
         patch('clothseg.np', DummyNP(), create=True):
        seg = ClothSegmenter(model_path='dummy')
        result = seg.parse(img_path)

    assert all(result[p] for p in ('upper_body', 'lower_body', 'full_body'))


def test_is_allowed_image_uses_mimetype():
    """File with disallowed extension should pass if mimetype is allowed."""
    f = File(io.BytesIO(PNG_BYTES), 'foo.bad')
    f.mimetype = 'image/png'
    assert app_module._is_allowed_image(f)


def test_parse_route_with_real_model(client):
    from clothseg import ClothSegmenter
    img_path = os.path.join(os.path.dirname(__file__), 'sample.png')

    class DummyArray:
        def __init__(self, arr):
            self.arr = arr

        def tolist(self):
            return self.arr

    class DummyTensor:
        def __init__(self, arr):
            self.array = arr

        def float(self):
            return self

        def permute(self, *axes):
            return self

        def unsqueeze(self, dim):
            return self

        def __truediv__(self, val):
            return self

        def __gt__(self, val):
            def convert(a):
                if isinstance(a, list):
                    return [convert(x) for x in a]
                return 1 if a > val else 0
            return DummyTensor(convert(self.array))

        def __getitem__(self, item):
            return DummyTensor(self.array[item])

        def squeeze(self):
            return self

        def cpu(self):
            return self

        def numpy(self):
            return DummyArray(self.array)

    class DummyModel:
        def __call__(self, tensor):
            h = len(tensor.array)
            w = len(tensor.array[0]) if h else 0
            ones = [[[1 for _ in range(w)] for _ in range(h)] for _ in range(3)]
            return DummyTensor([ones])

        def eval(self):
            pass

    class DummyTorch:
        def __init__(self):
            self.jit = types.SimpleNamespace(load=lambda path: DummyModel())

        def from_numpy(self, arr):
            return DummyTensor(arr)

        def no_grad(self):
            return contextlib.nullcontext()

    class DummyImage:
        def open(self, path):
            class Img:
                def convert(self, mode):
                    return self
            return Img()

    class DummyNP:
        def array(self, img):
            return [[[0]]]

    with patch('clothseg.torch', DummyTorch(), create=True), \
         patch('clothseg.Image', DummyImage(), create=True), \
         patch('clothseg.np', DummyNP(), create=True):
        seg = ClothSegmenter(model_path='dummy')
        with patch.object(app_module, 'cloth_segmenter', seg):
            with open(img_path, 'rb') as fh:
                data = {'image': (fh, 'sample.png')}
                response = client.post('/parse', data=data, content_type='multipart/form-data')

    assert response.status_code == 200
    payload = response.get_json()
    assert all(payload['parts'][p] for p in ('upper_body', 'lower_body', 'full_body'))
