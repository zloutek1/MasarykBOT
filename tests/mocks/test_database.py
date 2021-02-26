import unittest
from datetime import datetime

from bot.cogs.utils.db import Record
from tests.mocks import database

class DatabaseMocksTests(unittest.TestCase):
    def test_missing_repr(self):
        self.assertIsInstance(database.MISSING, database._MISSING_TYPE)
        self.assertEqual(repr(database.MISSING), "MISSING")

    def test_field_repr(self):
        field = database.Field(1)
        field.name = "a"
        field.type = int

        self.assertEqual(repr(field), f"Field(name='a',type={int},default=1)")

    def test_MockDatabase(self):
        db = database.MockDatabase()
        table = db.guilds

        self.assertIsInstance(table.select, unittest.mock.AsyncMock)
        self.assertIsInstance(table.insert, unittest.mock.AsyncMock)
        self.assertIsInstance(table.update, unittest.mock.AsyncMock)
        self.assertIsInstance(table.delete, unittest.mock.AsyncMock)
        self.assertIsInstance(table.soft_delete, unittest.mock.AsyncMock)

    def test_MockLeaderboardRecord_no_arguments(self):
        with self.assertRaises(TypeError) as context:
            record = database.MockLeaderboardRecord()
            self.assertTrue('missing 4 required positional arguments' in str(context.exception))

    def test_MockLeaderboardRecord_with_positional_arguments(self):
        with self.assertRaises(TypeError) as context:
            record = database.MockLeaderboardRecord(1, 2, 3, 4)
            self.assertTrue('takes 1 positional argument' in str(context.exception))


    def test_MockLeaderboardRecord(self):
        record = database.MockLeaderboardRecord(
            row_number=1,
            author_id=123456,
            author="Bob",
            sent_total=12_158_120
        )

        self.assertIsInstance(record, Record)

        self.assertEqual(record['row_number'], 1)
        self.assertEqual(record['author_id'], 123456)
        self.assertEqual(record['author'], "Bob")
        self.assertEqual(record['sent_total'], 12_158_120)

        self.assertEqual(record.get('row_number'), 1)
        self.assertEqual(record.get('author_id'), 123456)
        self.assertEqual(record.get('author'), "Bob")
        self.assertEqual(record.get('sent_total'), 12_158_120)


    def test_MockSubjectRecord_no_arguments(self):
        with self.assertRaises(TypeError) as context:
            record = database.MockSubjectRecord()
            self.assertTrue('missing 4 required positional arguments' in str(context.exception))

    def test_MockSubjectRecord_with_positional_arguments(self):
        with self.assertRaises(TypeError) as context:
            record = database.MockSubjectRecord(1, 2, 3, 4)
            self.assertTrue('takes 1 positional argument' in str(context.exception))


    def test_MockSubjectRecord(self):
        record = database.MockSubjectRecord(
            faculty="FI",
            code="IB000",
            name="MZI",
            url="muni.cz/fi/ib/000",
            terms=["podzim 2020"],
            created_at=datetime(2020, 10, 11)
        )

        self.assertIsInstance(record, Record)

        self.assertEqual(record['faculty'], "FI")
        self.assertEqual(record['code'], "IB000")
        self.assertEqual(record['name'], "MZI")
        self.assertEqual(record['url'], "muni.cz/fi/ib/000")
        self.assertListEqual(record['terms'], ["podzim 2020"])
        self.assertEqual(record['created_at'], datetime(2020, 10, 11))
        self.assertIsNone(record['edited_at'])
        self.assertIsNone(record['deleted_at'])

        self.assertEqual(record.get('faculty'), "FI")
        self.assertEqual(record.get('code'), "IB000")
        self.assertEqual(record.get('name'), "MZI")
        self.assertEqual(record.get('url'), "muni.cz/fi/ib/000")
        self.assertListEqual(record.get('terms'), ["podzim 2020"])
        self.assertEqual(record.get('created_at'), datetime(2020, 10, 11))
        self.assertIsNone(record.get('edited_at'))
        self.assertIsNone(record.get('deleted_at'))


    def test_MockSubjectRegisteredRecord_no_arguments(self):
        with self.assertRaises(TypeError) as context:
            record = database.MockSubjectRegisteredRecord()
            self.assertTrue('missing 4 required positional arguments' in str(context.exception))

    def test_MockSubjectRegisteredRecord_with_positional_arguments(self):
        with self.assertRaises(TypeError) as context:
            record = database.MockSubjectRegisteredRecord(1, 2, 3, 4)
            self.assertTrue('takes 1 positional argument' in str(context.exception))


    def test_MockSubjectRegisteredRecord(self):
        record = database.MockSubjectRegisteredRecord(
            faculty="FI",
            code="IB000",
            guild_id=123,
            member_ids=[12, 13, 14]
        )

        self.assertIsInstance(record, Record)

        self.assertEqual(record['faculty'], "FI")
        self.assertEqual(record['code'], "IB000")
        self.assertEqual(record['guild_id'], 123)
        self.assertListEqual(record['member_ids'], [12, 13, 14])

        self.assertEqual(record.get('faculty'), "FI")
        self.assertEqual(record.get('code'), "IB000")
        self.assertEqual(record.get('guild_id'), 123)
        self.assertListEqual(record.get('member_ids'), [12, 13, 14])


    def test_MockSubjectServerRecord_no_arguments(self):
        with self.assertRaises(TypeError) as context:
            record = database.MockSubjectServerRecord()
            self.assertTrue('missing 4 required positional arguments' in str(context.exception))

    def test_MockSubjectServerRecord_with_positional_arguments(self):
        with self.assertRaises(TypeError) as context:
            record = database.MockSubjectServerRecord(1, 2, 3, 4)
            self.assertTrue('takes 1 positional argument' in str(context.exception))


    def test_MockSubjectServerRecord(self):
        record = database.MockSubjectServerRecord(
            faculty="FI",
            code="IB111",
            guild_id=98798,
            category_id=None,
            channel_id=4568,
            voice_channel_id=None
        )

        self.assertIsInstance(record, Record)

        self.assertEqual(record['faculty'], "FI")
        self.assertEqual(record['code'], "IB111")
        self.assertEqual(record['guild_id'], 98798)
        self.assertIsNone(record['category_id'])
        self.assertEqual(record['channel_id'], 4568)
        self.assertIsNone(record['voice_channel_id'])

        self.assertEqual(record.get('faculty'), "FI")
        self.assertEqual(record.get('code'), "IB111")
        self.assertEqual(record.get('guild_id'), 98798)
        self.assertIsNone(record.get('category_id'))
        self.assertEqual(record.get('channel_id'), 4568)
        self.assertIsNone(record.get('voice_channel_id'))