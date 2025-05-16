
def fixture(func):
    """Simple decorator to mark a function as a test fixture."""
    func.__pytest_fixture__ = True
    return func
