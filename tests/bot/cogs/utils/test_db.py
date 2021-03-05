import unittest
from unittest.mock import patch, AsyncMock

from bot.cogs.utils import db
from tests.mocks.discord import (
    MockGuild,
    MockCategoryChannel,
    MockRole,
    MockMember,
    MockTextChannel,
    MockMessage,
    MockAttachment,
    MockReaction,
    MockEmoji,
    MockPartialEmoji
)
from tests.mocks.database import (
    MockPool,
    MockGuildRecord,
    MockCategoryRecord,
    MockRoleRecord,
    MockMemberRecord,
    MockChannelRecord,
    MockMessageRecord,
    MockAttachmentRecord,
    MockEmojiRecord,
    MockReactionRecord
)

import os
from discord import Color
from datetime import datetime
from contextlib import suppress
from functools import wraps

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
            created_at=datetime(2020, 9, 13, 12, 50, 42))

        expected = (8, 9, 10, "Hello world", datetime(2020, 9, 13, 12, 50, 42))
        actual = await table.prepare_one(message)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([message])
        self.assertListEqual([expected], actual)

        message.edited_at = None
        expected = (8, 9, 10, "Hello world", datetime(2020, 9, 13, 12, 50, 42))
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
        emoji = MockEmoji(id=8, name="kek", url="http://discord.gg/emoji", animated=True, created_at=datetime(2020, 9, 13, 12, 50, 42))

        expected = (8, "kek", "http://discord.gg/emoji", True)
        actual = await table.prepare_one(emoji)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([emoji])
        self.assertListEqual([expected], actual)

    async def test_emojis_prepare_partial_emoji(self):
        table = db.Emojis(MockPool())
        emoji = MockPartialEmoji(id=8, name="kek", url="http://discord.gg/emoji", animated=False, created_at=datetime(2020, 9, 13, 12, 50, 42))

        expected = (8, "kek", "http://discord.gg/emoji", False)
        actual = await table.prepare_one(emoji)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([emoji])
        self.assertListEqual([expected], actual)

    @patch('bot.cogs.utils.db.datetime', FixedDate)
    async def test_emojis_prepare_unicode_emoji(self):
        from emoji import demojize

        table = db.Emojis(MockPool())
        emoji = '😃'

        expected = (0x1f603, "grinning_face_with_big_eyes", "https://unicode.org/emoji/charts/full-emoji-list.html#1f603", False)
        actual = await table.prepare_one(emoji)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([emoji])
        self.assertListEqual([expected], actual)

    @patch('bot.cogs.utils.db.datetime', FixedDate)
    async def test_emojis_prepare_unicode_emoji_maltichar(self):
        from emoji import demojize

        table = db.Emojis(MockPool())
        emoji = '🇬🇧'

        expected = (0x1f1ec + 0x1f1e7, "United_Kingdom", "https://unicode.org/emoji/charts/full-emoji-list.html#1f1ec_1f1e7", False)
        actual = await table.prepare_one(emoji)
        self.assertTupleEqual(expected, actual)

        actual = await table.prepare([emoji])
        self.assertListEqual([expected], actual)

    async def test_emojis_prepare_from_message(self):
        table = db.Emojis(MockPool())
        message = MockMessage(id=11, content="Regular: <:kek:123>, animated: <a:pepega:159>, unicode: 😃")

        expected = [
            (123, "kek", "https://cdn.discordapp.com/emojis/123.png", False),
            (159, "pepega", "https://cdn.discordapp.com/emojis/159.gif", True),
            (0x1f603, "grinning_face_with_big_eyes", "https://unicode.org/emoji/charts/full-emoji-list.html#1f603", False),
        ]
        actual = await table.prepare_from_message(message)
        self.assertListEqual(expected, actual)

    async def test_message_emojis_prepare_from_message(self):
        table = db.MessageEmojis(MockPool())
        message = MockMessage(id=11, content="Regular: <:kek:123>, animated: <a:pepega:159>, emoji: 1. 😃 2. 😃 3. 😃")

        expected = [(11, 123, 1), (11, 159, 1), (11, 0x1f603, 3)]
        actual = await table.prepare_from_message(message)
        self.assertListEqual(expected, actual)

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
    @wraps(func)
    async def wrapper(self, conn):
        with suppress(FailTransaction):
            async with conn.transaction():
                await func(self, conn)
                raise FailTransaction("rollback changes made by the function")
    return wrapper

class TestQueries(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        try:
            url = os.getenv("POSTGRES")
            if url is None:
                self.skipTest("No .env file found with postgres url")

            self.db = db.Database.connect(url)
        except OSError as e:
            self.skipTest("Failed to connect to the database " + str(e))

        self.pool = self.db.pool

    async def asyncTearDown(self):
        await self.db.pool.close()

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
        self.roles = [
            (8, 10, "@everyone", "0x0", datetime(2020, 9, 20)),
            (8, 11, "Admin", "0xf1c40f", datetime(2020, 9, 22))
        ]

        self.select = self.db.roles.select.__wrapped__
        self.insert = self.db.roles.insert.__wrapped__
        self.update = self.db.roles.update.__wrapped__
        self.soft_delete = self.db.roles.soft_delete.__wrapped__

    async def _prepare_data(self, conn):
        self.guild = (8, "Main Guild", "http://image.jpg", datetime(2020, 9, 20))
        await self.db.guilds.insert.__wrapped__(self.db.guilds, conn, [self.guild])

    @db.withConn
    @failing_transaction
    async def test_insert(self, conn):
        await self._prepare_data(conn)
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
        await self._prepare_data(conn)
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
        await self._prepare_data(conn)
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
        self.channels = [
            (8, 9, 10, "general", 1, datetime(2020, 9, 22)),
            (8, None, 11, "talk", 2, datetime(2020, 9, 21))
        ]

        self.select = self.db.channels.select.__wrapped__
        self.insert = self.db.channels.insert.__wrapped__
        self.update = self.db.channels.update.__wrapped__
        self.soft_delete = self.db.channels.soft_delete.__wrapped__

    async def _prepare_data(self, conn):
        self.guild = (8, "Main Guild", "http://image.jpg", datetime(2020, 9, 20))
        await self.db.guilds.insert.__wrapped__(self.db.guilds, conn, [self.guild])

        self.category = (8, 9, "Main Category", 1, datetime(2020, 9, 20))
        await self.db.categories.insert.__wrapped__(self.db.categories, conn, [self.category])

    @db.withConn
    @failing_transaction
    async def test_insert(self, conn):
        await self._prepare_data(conn)
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
        await self._prepare_data(conn)
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
        await self._prepare_data(conn)
        _self = self.db.channels

        await self.insert(_self, conn, self.channels)
        actual = await self.select(_self, conn, 11)
        for row in actual:
            self.assertIsNone(row["deleted_at"])

        await self.soft_delete(_self, conn, [(11,)])
        actual = await self.select(_self, conn, 11)
        for row in actual:
            self.assertIsNotNone(row["deleted_at"])


class TestMessageQueries(TestQueries):
    async def asyncSetUp(self):
        self.messages = [
            (10, 9, 11, "First message", datetime(2020, 9, 22)),
            (10, 9, 12, "Second message", datetime(2020, 9, 21))
        ]

        self.select = self.db.messages.select.__wrapped__
        self.insert = self.db.messages.insert.__wrapped__
        self.update = self.db.messages.update.__wrapped__
        self.soft_delete = self.db.messages.soft_delete.__wrapped__

    async def _prepare_data(self, conn):
        self.guild = (8, "Main Guild", "http://image.jpg", datetime(2020, 9, 20))
        await self.db.guilds.insert.__wrapped__(self.db.guilds, conn, [self.guild])

        self.member = (9, "Sender1", "http://avatar.jpg", datetime(2020, 9, 20))
        await self.db.members.insert.__wrapped__(self.db.members, conn, [self.member])

        self.channel = (8, None, 10, "general", 1, datetime(2020, 9, 20))
        await self.db.channels.insert.__wrapped__(self.db.channels, conn, [self.channel])

    @db.withConn
    @failing_transaction
    async def test_insert(self, conn):
        await self._prepare_data(conn)
        _self = self.db.messages

        await self.insert(_self, conn, self.messages)
        actual = await self.select(_self, conn, 11)

        expected = [MockMessageRecord(
            channel_id=10,
            author_id=9,
            id=11,
            content="First message",
            created_at=datetime(2020, 9, 22),
            edited_at=None,
            deleted_at=None)]

        self.assertListEqual(actual, expected)

    @db.withConn
    @failing_transaction
    async def test_update(self, conn):
        await self._prepare_data(conn)
        _self = self.db.messages

        updated_messages = [
            (10, 9, 11, "Edited message", datetime(2020, 9, 22)),
        ]

        await self.insert(_self, conn, self.messages)
        await self.update(_self, conn, updated_messages)
        actual = await self.select(_self, conn, 11)

        row = next(filter(lambda row: row["id"] == 11, actual))
        self.assertEqual(row["content"], "Edited message")
        self.assertIsNotNone(row["edited_at"])

    @db.withConn
    @failing_transaction
    async def test_soft_delete(self, conn):
        await self._prepare_data(conn)
        _self = self.db.messages

        await self.insert(_self, conn, self.messages)
        actual = await self.select(_self, conn, 11)
        for row in actual:
            self.assertIsNone(row["deleted_at"])

        await self.soft_delete(_self, conn, [(11,)])
        actual = await self.select(_self, conn, 11)
        for row in actual:
            self.assertIsNotNone(row["deleted_at"])


class TestAttachmentQueries(TestQueries):
    async def asyncSetUp(self):
        self.attachments = [
            (11, 12, "file.txt", "http://discord.gg/file.txt"),
            (11, 13, "image.jpg", "http://discord.gg/image.jpg")
        ]

        self.select = self.db.attachments.select.__wrapped__
        self.insert = self.db.attachments.insert.__wrapped__

    async def _prepare_data(self, conn):
        self.guild = (8, "Main Guild", "http://image.jpg", datetime(2020, 9, 20))
        await self.db.guilds.insert.__wrapped__(self.db.guilds, conn, [self.guild])

        self.member = (9, "Sender1", "http://avatar.jpg", datetime(2020, 9, 20))
        await self.db.members.insert.__wrapped__(self.db.members, conn, [self.member])

        self.channel = (8, None, 10, "general", 1, datetime(2020, 9, 20))
        await self.db.channels.insert.__wrapped__(self.db.channels, conn, [self.channel])

        self.message = (10, 9, 11, "First message", datetime(2020, 9, 22))
        await self.db.messages.insert.__wrapped__(self.db.messages, conn, [self.message])

    @db.withConn
    @failing_transaction
    async def test_insert(self, conn):
        await self._prepare_data(conn)
        _self = self.db.attachments

        await self.insert(_self, conn, self.attachments)
        actual = await self.select(_self, conn, 12)

        expected = [MockAttachmentRecord(
            message_id=11,
            id=12,
            filename="file.txt",
            url="http://discord.gg/file.txt")]

        self.assertListEqual(actual, expected)


class TestEmojiQueries(TestQueries):
    async def asyncSetUp(self):
        self.emojis = [
            (9, "kek", "http://discord.gg/kek", False),
            (10, "pog", "http:/discord.gg/pog", False)
        ]

        self.select = self.db.emojis.select.__wrapped__
        self.insert = self.db.emojis.insert.__wrapped__
        self.update = self.db.emojis.update.__wrapped__
        self.soft_delete = self.db.emojis.soft_delete.__wrapped__

    @db.withConn
    @failing_transaction
    async def test_insert(self, conn):
        _self = self.db.emojis

        await self.insert(_self, conn, self.emojis)
        actual = await self.select(_self, conn, 9)

        expected = [MockEmojiRecord(
            id=9,
            name="kek",
            url="http://discord.gg/kek",
            animated=False,
            edited_at=None)]

        self.assertListEqual(actual, expected)

    @db.withConn
    @failing_transaction
    async def test_update(self, conn):
        _self = self.db.emojis

        updated_emojis = [
            (9, "pepega", "http://discord.gg/pepega", True),
        ]

        await self.insert(_self, conn, self.emojis)
        await self.update(_self, conn, updated_emojis)
        actual = await self.select(_self, conn, 9)

        row = next(filter(lambda row: row["id"] == 9, actual))
        self.assertEqual(row["name"], "pepega")
        self.assertEqual(row["url"], "http://discord.gg/pepega")
        self.assertTrue(row["animated"])
        self.assertIsNotNone(row["edited_at"])

class TestReactionQueries(TestQueries):
    async def asyncSetUp(self):
        self.reactions = [
            (11, 12, [9], datetime(2020, 9, 20)),
            (11, 13, [9], datetime(2020, 9, 20))
        ]

        self.select = self.db.reactions.select.__wrapped__
        self.insert = self.db.reactions.insert.__wrapped__
        self.update = self.db.reactions.update.__wrapped__
        self.soft_delete = self.db.reactions.soft_delete.__wrapped__

    async def _prepare_data(self, conn):
        self.guild = (8, "Main Guild", "http://image.jpg", datetime(2020, 9, 20))
        await self.db.guilds.insert.__wrapped__(self.db.guilds, conn, [self.guild])

        self.members = [
            (100, "OP", "http://avatar2.jpg", datetime(2020, 9, 20)),
            (9, "Sender1", "http://avatar.jpg", datetime(2020, 9, 20))
        ]
        await self.db.members.insert.__wrapped__(self.db.members, conn, self.members)

        self.channel = (8, None, 10, "general", 1, datetime(2020, 9, 20))
        await self.db.channels.insert.__wrapped__(self.db.channels, conn, [self.channel])

        self.message = (10, 9, 11, "First message", datetime(2020, 9, 22))
        await self.db.messages.insert.__wrapped__(self.db.messages, conn, [self.message])

        self.emojis = [
            (12, "kek", "http://discord.gg/kek", False),
            (13, "pog", "http:/discord.gg/pog", False)
        ]
        await self.db.emojis.insert.__wrapped__(self.db.emojis, conn, self.emojis)

    @db.withConn
    @failing_transaction
    async def test_insert(self, conn):
        await self._prepare_data(conn)
        _self = self.db.reactions

        await self.insert(_self, conn, self.reactions)
        actual = await self.select(_self, conn, 11, 12)

        expected = [MockReactionRecord(
            message_id=11,
            emoji_id=12,
            member_ids=[9],
            created_at=datetime(2020, 9, 20),
            edited_at=None,
            deleted_at=None
        )]

        self.assertListEqual(actual, expected)

    @db.withConn
    @failing_transaction
    async def test_update(self, conn):
        await self._prepare_data(conn)
        _self = self.db.reactions

        updated_reactions = [
            (11, 12, [100], datetime(2020, 9, 20)),
        ]

        await self.insert(_self, conn, self.reactions)
        await self.update(_self, conn, updated_reactions)
        actual = await self.select(_self, conn, 11, 12)

        row = next(filter(lambda row: row["message_id"] == 11 and row["emoji_id"] == 12, actual))
        self.assertListEqual(row["member_ids"], [100])
        self.assertIsNotNone(row["edited_at"])


    @db.withConn
    @failing_transaction
    async def test_soft_delete(self, conn):
        await self._prepare_data(conn)
        _self = self.db.reactions

        await self.insert(_self, conn, self.reactions)
        actual = await self.select(_self, conn, 11, 12)
        for row in actual:
            self.assertIsNone(row["deleted_at"])

        await self.soft_delete(_self, conn, [(11, 12)])
        actual = await self.select(_self, conn, 11, 12)
        for row in actual:
            self.assertIsNotNone(row["deleted_at"])
