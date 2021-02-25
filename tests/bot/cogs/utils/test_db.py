import unittest
from unittest.mock import patch

from bot.cogs.utils import db
from tests.mocks.discord import MockGuild, MockCategoryChannel, MockRole, MockMember, MockTextChannel, MockMessage, MockAttachment, MockReaction, MockEmoji, MockPartialEmoji
from tests.mocks.database import MockPool

from discord import Color
from datetime import datetime

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
