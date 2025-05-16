class Response:
    def __init__(self, content=b'', status_code=200, headers=None):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception('error')

def post(url, files=None, data=None):
    raise NotImplementedError('requests.post not implemented')
