import unittest
import unittest.mock

from tests.mocks import helpers

class HelpersdMocksTests(unittest.TestCase):
    def test_MockReturnFunc(self):
        def true_once():
            yield True
            yield False

        true_func = helpers.MockReturnFunc(true_once)
        self.assertTrue(true_func())
        self.assertFalse(true_func())
        self.assertIsNone(true_func())
        self.assertIsNone(true_func())
