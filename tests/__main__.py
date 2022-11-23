import pytest

def load_tests(loader, tests, pattern):
    return loader.discover('.')

if __name__ == '__main__':
    exit_code = pytest.main(["--cov-report", "xml:cov.xml", "--cov", ".", "-s"])
    exit(int(exit_code))