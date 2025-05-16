def secure_filename(name: str) -> str:
    return name.replace('..', '').replace('/', '')
