import unittest.mock

import inject
import pytest

from bot.db import Pool


def setup_mock_injections():
    inject.configure(lambda binder: binder.bind(Pool, unittest.mock.Mock(Pool)))


def load_tests(loader, tests, pattern):
    return loader.discover('.')



if __name__ == '__main__':
    setup_mock_injections()
    exit_code = pytest.main(["--cov-report", "xml:cov.xml", "--cov", ".", "-s"])
    exit(int(exit_code))
