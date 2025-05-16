import importlib
import inspect
import os
import sys
import traceback

PACKAGE_DIR = os.path.dirname(__file__)
TESTS_DIR = os.path.join(os.path.dirname(PACKAGE_DIR), 'tests')


def load_module_tests(module):
    tests = []
    fixtures = {}
    for name in dir(module):
        obj = getattr(module, name)
        if callable(obj):
            if getattr(obj, '__pytest_fixture__', False):
                fixtures[name] = obj
            elif name.startswith('test_'):
                tests.append(obj)
    return tests, fixtures


def run_tests():
    passed = 0
    failed = 0
    test_files = [f for f in os.listdir(TESTS_DIR) if f.startswith('test_') and f.endswith('.py')]
    sys.path.insert(0, os.path.dirname(PACKAGE_DIR))
    for fname in test_files:
        module_name = f"tests.{fname[:-3]}"
        module = importlib.import_module(module_name)
        tests, fixtures = load_module_tests(module)
        for test in tests:
            sig = inspect.signature(test)
            kwargs = {}
            generators = {}
            for param in sig.parameters.values():
                if param.name in fixtures:
                    fixture_func = fixtures[param.name]
                    if inspect.isgeneratorfunction(fixture_func):
                        gen = fixture_func()
                        val = next(gen)
                        generators[param.name] = gen
                    else:
                        val = fixture_func()
                    kwargs[param.name] = val
            try:
                test(**kwargs)
                print('.', end='')
                passed += 1
            except Exception:
                print('F', end='')
                failed += 1
                traceback.print_exc()
            finally:
                for gen in generators.values():
                    try:
                        next(gen)
                    except StopIteration:
                        pass
    print()
    if failed:
        print(f"{passed} passed, {failed} failed")
        return 1
    else:
        print(f"{passed} passed")
        return 0


def main():
    status = run_tests()
    sys.exit(status)


if __name__ == '__main__':
    main()
