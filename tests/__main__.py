import pytest

def load_tests(loader, tests, pattern):
    return loader.discover('.')

if __name__ == '__main__':
    pytest.main(["--cov-report", "xml:cov.xml", "--cov", "."])