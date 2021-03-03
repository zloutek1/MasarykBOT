import unittest
from unittest.mock import patch, AsyncMock

from bot.cogs.utils import db
from tests.mocks.discord import MockGuild, MockCategoryChannel, MockRole, MockMember, MockTextChannel, MockMessage, MockAttachment, MockReaction, MockEmoji, MockPartialEmoji
from tests.mocks.database import MockPool, MockGuildRecord, MockCategoryRecord, MockRoleRecord, MockMemberRecord, MockChannelRecord

import os
from discord import Color
from datetime import datetime
from dotenv import load_dotenv
from contextlib import suppress

class FixedDate(datetime):
    @classmethod
    def now(cls):
        return datetime(2020, 9, 13, 12, 50, 42)


class DBTests(unittest.IsolatedAsyncioTestCase):
    async def test_guild_prepare(self):
        table = db.Guilds(MockPool())
        guild = MockGuild(id=8, name="TEST", icon_url="http://www.image.com", created_at=datetime(2020, 9, 13, 12, 50, 42))

        expected = (8, "TEST", "http://www.image.com", datetime(2020, 9, 13, 12, 50, 42))
        actual = await table.prepare_one(guild)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([guild])
        self.assertListEqual([expected], actual)

    async def test_category_prepare(self):
        table = db.Categories(MockPool())
        category = MockCategoryChannel(id=10, name="CAT", guild=MockGuild(id=8), position=2, created_at=datetime(2020, 9, 13, 12, 50, 42))

        expected = (8, 10, "CAT", 2, datetime(2020, 9, 13, 12, 50, 42))
        actual = await table.prepare_one(category)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([category])
        self.assertListEqual([expected], actual)

    async def test_role_prepare(self):
        table = db.Roles(MockPool())
        role = MockRole(id=10, name="everyone", guild=MockGuild(id=8), color=Color(0xdeadbf), created_at=datetime(2020, 9, 13, 12, 50, 42))

        expected = (8, 10, "everyone", '0xdeadbf', datetime(2020, 9, 13, 12, 50, 42))
        actual = await table.prepare_one(role)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([role])
        self.assertListEqual([expected], actual)

    async def test_member_prepare(self):
        table = db.Members(MockPool())
        member = MockMember(id=10, name="Bob", avatar_url="http://www.image.com", created_at=datetime(2020, 9, 13, 12, 50, 42))

        expected = (10, "Bob", 'http://www.image.com', datetime(2020, 9, 13, 12, 50, 42))
        actual = await table.prepare_one(member)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([member])
        self.assertListEqual([expected], actual)

    async def test_channel_prepare(self):
        table = db.Channels(MockPool())
        channel = MockTextChannel(id=10, name="general", guild=MockGuild(id=8), category=MockCategoryChannel(id=9), position=2, created_at=datetime(2020, 9, 13, 12, 50, 42))

        expected = (8, 9, 10, "general", 2, datetime(2020, 9, 13, 12, 50, 42))
        actual = await table.prepare_one(channel)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([channel])
        self.assertListEqual([expected], actual)

        channel.category = None
        expected = (8, None, 10, "general", 2, datetime(2020, 9, 13, 12, 50, 42))
        actual = await table.prepare_one(channel)
        self.assertTupleEqual(expected, actual)

    async def test_message_prepare(self):
        table = db.Messages(MockPool())
        message = MockMessage(
            id=10,
            content="Hello world",
            channel=MockTextChannel(id=8, name="general"),
            author=MockMember(id=9, name="Bob"),
            created_at=datetime(2020, 9, 13, 12, 50, 42),
            edited_at=datetime(2020, 9, 14, 12, 50, 42))

        expected = (8, 9, 10, "Hello world", datetime(2020, 9, 13, 12, 50, 42), datetime(2020, 9, 14, 12, 50, 42))
        actual = await table.prepare_one(message)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([message])
        self.assertListEqual([expected], actual)

        message.edited_at = None
        expected = (8, 9, 10, "Hello world", datetime(2020, 9, 13, 12, 50, 42), None)
        actual = await table.prepare_one(message)
        self.assertTupleEqual(expected, actual)

    async def test_attachment_prepare(self):
        table = db.Attachments(MockPool())
        attachment = MockAttachment(id=10, filename="file.txt", url="discord.gg/file.txt")

        expected = (10, "file.txt", "discord.gg/file.txt")
        actual = await table.prepare_one(attachment)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([attachment])
        self.assertListEqual([expected], actual)

    async def test_emojis_prepare_full_emoji(self):
        table = db.Emojis(MockPool())
        emoji = MockEmoji(id=8, name="kek", url="http://discord.gg/emoji", created_at=datetime(2020, 9, 13, 12, 50, 42), animated=True)

        expected = (8, "kek", "http://discord.gg/emoji", datetime(2020, 9, 13, 12, 50, 42), True)
        actual = await table.prepare_one(emoji)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([emoji])
        self.assertListEqual([expected], actual)


    async def test_emojis_prepare_partial_emoji(self):
        table = db.Emojis(MockPool())
        emoji = MockPartialEmoji(id=8, name="kek", url="http://discord.gg/emoji", created_at=datetime(2020, 9, 13, 12, 50, 42), animated=False)

        expected = (8, "kek", "http://discord.gg/emoji", datetime(2020, 9, 13, 12, 50, 42), False)
        actual = await table.prepare_one(emoji)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([emoji])
        self.assertListEqual([expected], actual)

    @patch('bot.cogs.utils.db.datetime', FixedDate)
    async def test_emojis_prepare_unicode_emoji(self):
        from emoji import demojize

        table = db.Emojis(MockPool())
        emoji = '😃'

        expected = (0x1f603, "grinning_face_with_big_eyes", "https://unicode.org/emoji/charts/full-emoji-list.html#1f603", datetime(2020, 9, 13, 12, 50, 42), False)
        actual = await table.prepare_one(emoji)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([emoji])
        self.assertListEqual([expected], actual)

    async def test_logger_with_process(self):
        table = db.Logger(MockPool())

        table.start_process = AsyncMock()
        table.mark_process_finished = AsyncMock()

        async with table.process(guild_id=10, from_date=datetime(2020, 9, 20), to_date=datetime(2020, 9, 27)):
            table.start_process.assert_called_once()
            table.mark_process_finished.assert_not_called()

        table.start_process.assert_called_once()
        table.mark_process_finished.assert_called_once()

class FailTransaction(Exception):
    pass

def failing_transaction(func):
    async def wrapper(self, conn):
        with suppress(FailTransaction):
            async with conn.transaction():
                await func(self, conn)
                raise FailTransaction("rollback changes made by the function")
    return wrapper

class TestQueries(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        load_dotenv()
        self.db = db.Database.connect(os.getenv("POSTGRES"))
        if self.db is None:
            self.skipTest("Failed to connect to the database")
        self.pool = self.db.pool

class TestGuildQueries(TestQueries):
    async def asyncSetUp(self):
        self.guilds = [
            (8, "Main Guild", "http://image.jpg", datetime(2020, 9, 20)),
            (156, "Second guild", "http://no-image.jpg", datetime(2020, 9, 22))
        ]

        self.select = self.db.guilds.select.__wrapped__
        self.insert = self.db.guilds.insert.__wrapped__
        self.update = self.db.guilds.update.__wrapped__
        self.soft_delete = self.db.guilds.soft_delete.__wrapped__

    @db.withConn
    @failing_transaction
    async def test_insert(self, conn):
        _self = self.db.guilds

        await self.insert(_self, conn, self.guilds)
        actual = await self.select(_self, conn, 8)

        expected = [MockGuildRecord(
            id=8,
            name="Main Guild",
            icon_url="http://image.jpg",
            created_at=datetime(2020, 9, 20),
            edited_at=None,
            deleted_at=None)]

        self.assertListEqual(actual, expected)

    @db.withConn
    @failing_transaction
    async def test_update(self, conn):
        _self = self.db.guilds

        updated_guilds = [
            (8, "New name", "http://image.png", datetime(2020, 9, 20))
        ]

        await self.insert(_self, conn, self.guilds)
        await self.update(_self, conn, updated_guilds)
        actual = await self.select(_self, conn, 8)

        row = next(filter(lambda row: row["id"] == 8, actual))
        self.assertEqual(row["name"], "New name")
        self.assertEqual(row["icon_url"], "http://image.png")
        self.assertIsNotNone(row["edited_at"])

    @db.withConn
    @failing_transaction
    async def test_soft_delete(self, conn):
        _self = self.db.guilds

        await self.insert(_self, conn, self.guilds)
        actual = await self.select(_self, conn, 8)
        for row in actual:
            self.assertIsNone(row["deleted_at"])

        await self.soft_delete(_self, conn, [(8,)])
        actual = await self.select(_self, conn, 8)
        for row in actual:
            self.assertIsNotNone(row["deleted_at"])


class TestCategoryQueries(TestQueries):
    async def asyncSetUp(self):
        self.guild = (8, "Main Guild", "http://image.jpg", datetime(2020, 9, 20))
        await self.db.guilds.insert([self.guild])

        self.categories = [
            (8, 10, "Category name", 1, datetime(2020, 9, 20)),
            (8, 11, "second category", 2, datetime(2020, 9, 22))
        ]

        self.select = self.db.categories.select.__wrapped__
        self.insert = self.db.categories.insert.__wrapped__
        self.update = self.db.categories.update.__wrapped__
        self.soft_delete = self.db.categories.soft_delete.__wrapped__

    @db.withConn
    @failing_transaction
    async def test_insert(self, conn):
        _self = self.db.categories

        await self.insert(_self, conn, self.categories)
        actual = await self.select(_self, conn, 10)

        expected = [MockCategoryRecord(
            guild_id=8,
            id=10,
            name="Category name",
            position=1,
            created_at=datetime(2020, 9, 20),
            edited_at=None,
            deleted_at=None)]

        self.assertListEqual(actual, expected)

    @db.withConn
    @failing_transaction
    async def test_update(self, conn):
        _self = self.db.categories

        updated_categories = [
            (8, 10, "New Category name", 3, datetime(2020, 9, 20)),
        ]

        await self.insert(_self, conn, self.categories)
        await self.update(_self, conn, updated_categories)
        actual = await self.select(_self, conn, 10)

        row = next(filter(lambda row: row["id"] == 10, actual))
        self.assertEqual(row["name"], "New Category name")
        self.assertEqual(row["position"], 3)
        self.assertIsNotNone(row["edited_at"])

    @db.withConn
    @failing_transaction
    async def test_soft_delete(self, conn):
        _self = self.db.categories

        await self.insert(_self, conn, self.categories)
        actual = await self.select(_self, conn, 10)
        for row in actual:
            self.assertIsNone(row["deleted_at"])

        await self.soft_delete(_self, conn, [(10,)])
        actual = await self.select(_self, conn, 10)
        for row in actual:
            self.assertIsNotNone(row["deleted_at"])


class TestRoleQueries(TestQueries):
    async def asyncSetUp(self):
        self.guild = (8, "Main Guild", "http://image.jpg", datetime(2020, 9, 20))
        await self.db.guilds.insert([self.guild])

        self.roles = [
            (8, 10, "@everyone", "0x0", datetime(2020, 9, 20)),
            (8, 11, "Admin", "0xf1c40f", datetime(2020, 9, 22))
        ]

        self.select = self.db.roles.select.__wrapped__
        self.insert = self.db.roles.insert.__wrapped__
        self.update = self.db.roles.update.__wrapped__
        self.soft_delete = self.db.roles.soft_delete.__wrapped__

    @db.withConn
    @failing_transaction
    async def test_insert(self, conn):
        _self = self.db.roles

        await self.insert(_self, conn, self.roles)
        actual = await self.select(_self, conn, 11)

        expected = [MockRoleRecord(
            guild_id=8,
            id=11,
            name="Admin",
            color='0xf1c40f',
            created_at=datetime(2020, 9, 22),
            edited_at=None,
            deleted_at=None)]

        self.assertListEqual(actual, expected)

    @db.withConn
    @failing_transaction
    async def test_update(self, conn):
        _self = self.db.roles

        updated_roles = [
            (8, 10, "@here", "0xffffff", datetime(2020, 9, 20)),
        ]

        await self.insert(_self, conn, self.roles)
        await self.update(_self, conn, updated_roles)
        actual = await self.select(_self, conn, 10)

        row = next(filter(lambda row: row["id"] == 10, actual))
        self.assertEqual(row["name"], "@here")
        self.assertEqual(row["color"], "0xffffff")
        self.assertIsNotNone(row["edited_at"])

    @db.withConn
    @failing_transaction
    async def test_soft_delete(self, conn):
        _self = self.db.roles

        await self.insert(_self, conn, self.roles)
        actual = await self.select(_self, conn, 11)
        for row in actual:
            self.assertIsNone(row["deleted_at"])

        await self.soft_delete(_self, conn, [(11,)])
        actual = await self.select(_self, conn, 11)
        for row in actual:
            self.assertIsNotNone(row["deleted_at"])


class TestMemberQueries(TestQueries):
    async def asyncSetUp(self):
        self.members = [
            (10, "First", "http://avatar.jpg", datetime(2020, 9, 20)),
            (11, "Hello", "http://avatar2.jpg", datetime(2020, 9, 22))
        ]

        self.select = self.db.members.select.__wrapped__
        self.insert = self.db.members.insert.__wrapped__
        self.update = self.db.members.update.__wrapped__
        self.soft_delete = self.db.members.soft_delete.__wrapped__

    @db.withConn
    @failing_transaction
    async def test_insert(self, conn):
        _self = self.db.members

        await self.insert(_self, conn, self.members)
        actual = await self.select(_self, conn, 11)

        expected = [MockMemberRecord(
            id=11,
            names=["Hello"],
            avatar_url="http://avatar2.jpg",
            created_at=datetime(2020, 9, 22),
            edited_at=None,
            deleted_at=None)]

        self.assertListEqual(actual, expected)

    @db.withConn
    @failing_transaction
    async def test_update(self, conn):
        _self = self.db.members

        updated_members = [
            (10, "Second", "http://avatar.png", datetime(2020, 9, 20)),
        ]

        await self.insert(_self, conn, self.members)
        await self.update(_self, conn, updated_members)
        actual = await self.select(_self, conn, 10)

        row = next(filter(lambda row: row["id"] == 10, actual))
        self.assertListEqual(row["names"], ["Second", "First"])
        self.assertEqual(row["avatar_url"], "http://avatar.png")
        self.assertIsNotNone(row["edited_at"])

    @db.withConn
    @failing_transaction
    async def test_soft_delete(self, conn):
        _self = self.db.members

        await self.insert(_self, conn, self.members)
        actual = await self.select(_self, conn, 11)
        for row in actual:
            self.assertIsNone(row["deleted_at"])

        await self.soft_delete(_self, conn, [(11,)])
        actual = await self.select(_self, conn, 11)
        for row in actual:
            self.assertIsNotNone(row["deleted_at"])


class TestChannelQueries(TestQueries):
    async def asyncSetUp(self):
        self.guild = (8, "Main Guild", "http://image.jpg", datetime(2020, 9, 20))
        await self.db.guilds.insert([self.guild])

        self.category = (8, 9, "Main Category", 1, datetime(2020, 9, 20))
        await self.db.categories.insert([self.category])

        self.channels = [
            (8, 9, 10, "general", 1, datetime(2020, 9, 22)),
            (8, None, 11, "talk", 2, datetime(2020, 9, 21))
        ]

        self.select = self.db.channels.select.__wrapped__
        self.insert = self.db.channels.insert.__wrapped__
        self.update = self.db.channels.update.__wrapped__
        self.soft_delete = self.db.channels.soft_delete.__wrapped__

    @db.withConn
    @failing_transaction
    async def test_insert(self, conn):
        _self = self.db.channels

        await self.insert(_self, conn, self.channels)
        actual = await self.select(_self, conn, 10)

        expected = [MockChannelRecord(
            guild_id=8,
            category_id=9,
            id=10,
            name="general",
            position=1,
            created_at=datetime(2020, 9, 22),
            edited_at=None,
            deleted_at=None)]

        self.assertListEqual(actual, expected)

    @db.withConn
    @failing_transaction
    async def test_update(self, conn):
        _self = self.db.channels

        updated_channels = [
            (8, 9, 10, "shitposting", 3, datetime(2020, 9, 22)),
        ]

        await self.insert(_self, conn, self.channels)
        await self.update(_self, conn, updated_channels)
        actual = await self.select(_self, conn, 10)

        row = next(filter(lambda row: row["id"] == 10, actual))
        self.assertEqual(row["name"], "shitposting")
        self.assertEqual(row["position"], 3)
        self.assertIsNotNone(row["edited_at"])

    @db.withConn
    @failing_transaction
    async def test_soft_delete(self, conn):
        _self = self.db.channels

        await self.insert(_self, conn, self.channels)
        actual = await self.select(_self, conn, 11)
        for row in actual:
            self.assertIsNone(row["deleted_at"])

        await self.soft_delete(_self, conn, [(11,)])
        actual = await self.select(_self, conn, 11)
        for row in actual:
            self.assertIsNotNone(row["deleted_at"])


