import unittest

from tests.mocks import database

class DatabaseMocksTests(unittest.TestCase):
    def setUp(self):
        @database.record
        def MockRecord(*, number: int, string: str, boolean: bool):
            pass

        self.MockRecord = MockRecord

    def test_valid_record(self):
        pass