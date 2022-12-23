from typing import Any
import unittest.mock

import inject
import pytest

from bot.db import Pool


def setup_global_mock_injections() -> None:
    def mock_db(binder: inject.Binder) -> None:
        binder.bind(Pool, unittest.mock.Mock(Pool))
    inject.configure(mock_db)


def load_tests(loader: Any, tests: Any, pattern: Any) -> Any:
    return loader.discover('.')



if __name__ == '__main__':
    setup_global_mock_injections()
    exit_code = pytest.main(["--cov-report", "xml:cov.xml", "--cov", ".", "-s"])
    exit(int(exit_code))
