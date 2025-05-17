import mimetypes


class Request:
    def __init__(self, form=None, files=None):
        self.form = form or {}
        self.files = files or {}


class File:
    def __init__(self, stream, filename):
        self.stream = stream
        self.filename = filename
        self.mimetype = mimetypes.guess_type(filename)[0]

    def save(self, path):
        with open(path, 'wb') as f:
            f.write(self.stream.read())
        self.stream.seek(0)


class Response:
    def __init__(self, data='', status=200, json=None):
        self.data = data
        self.status_code = status
        self._json = json

    def get_json(self):
        return self._json


request = Request()


def jsonify(obj):
    return Response(json=obj, status=200)


def render_template(name):
    return Response(f'rendered {name}', status=200)


class Flask:
    def __init__(self, name):
        self.name = name
        self.config = {}
        self.routes = {}

    def route(self, path, methods=None):
        if methods is None:
            methods = ['GET']

        def decorator(func):
            for method in methods:
                self.routes[(method, path)] = func
            return func
        return decorator

    def test_client(self):
        app = self

        class Client:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                pass

            def open(self, path, method='GET', data=None, content_type=None):
                global request
                form = {}
                files = {}
                if method == 'POST' and data:
                    for k, v in data.items():
                        if isinstance(v, tuple) and len(v) == 2:
                            files[k] = File(v[0], v[1])
                        else:
                            form[k] = v
                request.form = form
                request.files = files
                view = app.routes.get((method, path))
                if not view:
                    return Response(status=404)
                rv = view()
                if isinstance(rv, Response):
                    return rv
                if isinstance(rv, tuple):
                    data, status = rv
                    if isinstance(data, Response):
                        data.status_code = status
                        return data
                    if isinstance(data, dict):
                        return Response(json=data, status=status)
                    return Response(data=str(data), status=status)
                if isinstance(rv, dict):
                    return Response(json=rv, status=200)
                return Response(data=str(rv), status=200)

            def get(self, path):
                return self.open(path, method='GET')

            def post(self, path, data=None, content_type=None):
                return self.open(path, method='POST', data=data, content_type=content_type)

        return Client()


def request_context():
    """Context manager placeholder for compatibility."""
    from contextlib import contextmanager
    @contextmanager
    def manager():
        yield
    return manager()
