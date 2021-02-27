import unittest
from unittest.mock import patch, call, AsyncMock

from emoji import demojize
from datetime import datetime, date

from bot.cogs.utils import db
from bot.cogs import logger

from tests.mocks.discord import (MockBot,
                                MockRole, MockMember, MockUser,
                                MockGuild, MockCategoryChannel, MockTextChannel,
                                MockMessage, MockAttachment, MockReaction, MockEmoji,
                                AsyncIterator)
from tests.mocks.database import MockDatabase, MockLoggerRecord
from tests.mocks.helpers import MockReturnFunc


class LoggerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        bot = MockBot()
        bot.db = MockDatabase()
        cog = logger.Logger(bot=bot)

        self.bot = bot
        self.cog = cog

    async def test_backup(self):
        self.cog.backup_guilds = AsyncMock()
        self.cog.backup_roles = AsyncMock()
        self.cog.backup_members = AsyncMock()
        self.cog.backup_categories = AsyncMock()
        self.cog.backup_channels = AsyncMock()
        self.cog.backup_messages = AsyncMock()

        channels = [
            MockTextChannel(id=12),
            MockTextChannel(id=14),
            MockTextChannel(id=15)
        ]

        guilds = [
            MockGuild(
                id = 11,
                roles=[MockRole(id=12)],
                members=[MockMember(id=13)],
                categories=[MockCategoryChannel(id=14)],
                text_channels = [channels[0]]
            ),
            MockGuild(
                id = 13,
                roles=[],
                members=[],
                categories=[],
                text_channels = [channels[1], channels[2]]
            )
        ]

        self.bot.guilds = guilds
        await self.cog.backup()

        self.cog.backup_guilds.assert_has_calls([
            call(guilds)
        ])
        self.cog.backup_roles.assert_has_calls([
            call(guilds[0].roles),
            call(guilds[1].roles)
        ])
        self.cog.backup_members.assert_has_calls([
            call(guilds[0].members),
            call(guilds[1].members)
        ])
        self.cog.backup_categories.assert_has_calls([
            call(guilds[0].categories),
            call(guilds[1].categories)
        ])
        self.cog.backup_channels.assert_has_calls([
            call(guilds[0].text_channels),
            call(guilds[1].text_channels)
        ])
        self.cog.backup_messages.assert_has_calls([call(channels[0]), call(channels[1]), call(channels[2])])

    async def test_backup_guilds(self):
        guilds = [
            MockGuild(id=11,   name="guild1", icon_url="http://icon.jpg", created_at=date.today()),
            MockGuild(id=158,  name="guild2", icon_url="http://icon2.jpg", created_at=date.today()),
            MockGuild(id=1548, name="guild3", icon_url="http://icon6.jpg", created_at=date(2010, 11, 12)),
        ]

        await self.cog.backup_guilds(guilds)

        self.bot.db.guilds.insert.assert_called_once_with([
            (11,   "guild1", "http://icon.jpg", date.today()),
            (158,  "guild2", "http://icon2.jpg", date.today()),
            (1548, "guild3", "http://icon6.jpg", date(2010, 11, 12))
        ])

    async def test_backup_categories(self):
        guild = MockGuild(id=8)
        categories = [
            MockCategoryChannel(guild=guild, id=10, name="category1", position=1, created_at=date.today()),
            MockCategoryChannel(guild=guild, id=11, name="category2", position=2, created_at=date.today()),
            MockCategoryChannel(guild=guild, id=12, name="category3", position=3, created_at=date(2010, 11, 12)),
        ]

        await self.cog.backup_categories(categories)

        self.bot.db.categories.insert.assert_called_once_with([
            (8, 10, "category1", 1, date.today()),
            (8, 11, "category2", 2, date.today()),
            (8, 12, "category3", 3, date(2010, 11, 12))
        ])

    async def test_backup_roles(self):
        guild = MockGuild(id=8)
        roles = [
            MockRole(guild=guild, id=10, name="Admin", color=0xfedc56, created_at=date.today()),
            MockRole(guild=guild, id=11, name="Member", created_at=date.today()),
            MockRole(guild=guild, id=12, name="everyone", created_at=date(2010, 11, 12)),
        ]

        await self.cog.backup_roles(roles)

        self.bot.db.roles.insert.assert_called_once_with([
            (8, 10, "Admin", hex(0xfedc56), date.today()),
            (8, 11, "Member", hex(0xdeadbf), date.today()),
            (8, 12, "everyone", hex(0xdeadbf), date(2010, 11, 12))
        ])

    async def test_backup_small_members(self):
        guild = MockGuild(id=8)
        members = [
            MockMember(guild=guild, id=10, name="User", avatar_url="http://image.png", discriminator="9010", created_at=date.today()),
            MockMember(guild=guild, id=11, name="Bob", avatar_url="http://image2.png", discriminator="1100", created_at=date.today()),
            MockMember(guild=guild, id=12, name="Zlo", avatar_url="http://image3.png", discriminator="0000", created_at=date(2010, 11, 12)),
        ]

        await self.cog.backup_members(members)

        self.bot.db.members.insert.assert_called_once_with([
            (10, "User", "http://image.png", date.today()),
            (11, "Bob", "http://image2.png", date.today()),
            (12, "Zlo", "http://image3.png", date(2010, 11, 12))
        ])

    async def test_backup_thousand_members(self):
        names = ["User", "Bob" "Zlo", "Four", "Five"]

        guild = MockGuild(id=8)
        members = [
            MockMember(guild=guild, id=index, name=names[index % len(names)], avatar_url="http://image.png", discriminator=f"{index:0>4}", created_at=date.today())
            for index in range(1_000)
        ]

        await self.cog.backup_members(members)

        def fmt(m):
            return m.id, m.name, m.avatar_url, m.created_at

        self.assertEqual(self.bot.db.members.insert.call_count, len(members) // 550 + 1)
        self.bot.db.members.insert.assert_has_calls([
            call(list(map(fmt, members[:550]))),
            call(list(map(fmt, members[550:])))
        ])

    async def test_backup_channels(self):
        guild = MockGuild(id=8)
        category = MockCategoryChannel(guild=guild, id=9)
        text_channels = [
            MockTextChannel(guild=guild, category=None, id=10, name="general", position=1, created_at=date.today()),
            MockTextChannel(guild=guild, category=None, id=11, name="fun", position=2, created_at=date.today()),
            MockTextChannel(guild=guild, category=category, id=12, name="nsfw", position=1, created_at=date(2010, 11, 12)),
        ]

        await self.cog.backup_channels(text_channels)

        self.bot.db.channels.insert.assert_called_once_with([
            (8, None, 10, "general", 1, date.today()),
            (8, None, 11, "fun", 2, date.today()),
            (8, 9, 12, "nsfw", 1, date(2010, 11, 12))
        ])

    @unittest.skip("integration test")
    async def test_messages(self):
        pass

    async def test_backup_failed_weeks(self):
        def generator():
            yield True
            yield True
            yield True
            yield False

        self.cog.backup_failed_week = AsyncMock()
        self.cog.backup_failed_week.side_effect = MockReturnFunc(generator)

        channel = MockTextChannel(id=8)
        with patch('bot.cogs.logger.asyncio.sleep'):
            await self.cog.backup_failed_weeks(channel)

        self.assertEqual(self.cog.backup_failed_week.call_count, 4)

    async def test_backup_failed_week(self):
        rows = [
            MockLoggerRecord(channel_id=1, from_date=datetime(2020, 9, 13), to_date=datetime(2020, 9, 20), finished_at=datetime(2020, 10, 12)),
            MockLoggerRecord(channel_id=1, from_date=datetime(2020, 9, 20), to_date=datetime(2020, 9, 27), finished_at=None),
            MockLoggerRecord(channel_id=1, from_date=datetime(2020, 9, 27), to_date=datetime(2020, 10, 4), finished_at=datetime(2020, 10, 12)),
            MockLoggerRecord(channel_id=1, from_date=datetime(2020, 10, 4), to_date=datetime(2020, 10, 11), finished_at=None),
            MockLoggerRecord(channel_id=1, from_date=datetime(2020, 10, 11), to_date=datetime(2020, 10, 18), finished_at=datetime(2020, 10, 12)),
        ]
        self.bot.db.logger.select.return_value = rows

        self.cog.backup_in_range = AsyncMock()

        channel = MockTextChannel(id=8)
        await self.cog.backup_failed_week(channel)

        self.cog.backup_in_range.assert_has_calls([
            call(channel, datetime(2020, 9, 20), datetime(2020, 9, 27)),
            call(channel, datetime(2020, 10, 4), datetime(2020, 10, 11))
        ])

    async def test_backup_new_weeks(self):
        def generator():
            yield True
            yield True
            yield True
            yield False

        self.cog.backup_new_week = AsyncMock()
        self.cog.backup_new_week.side_effect = MockReturnFunc(generator)

        channel = MockTextChannel(id=8)
        with patch('bot.cogs.logger.asyncio.sleep'):
            await self.cog.backup_new_weeks(channel)

        self.assertEqual(self.cog.backup_new_week.call_count, 4)

    async def test_get_latest_finished_week(self):
        rows = [
            MockLoggerRecord(channel_id=1, from_date=datetime(2020, 9, 13), to_date=datetime(2020, 9, 20), finished_at=datetime(2020, 10, 12)),
            MockLoggerRecord(channel_id=1, from_date=datetime(2020, 9, 20), to_date=datetime(2020, 9, 27), finished_at=None),
            MockLoggerRecord(channel_id=1, from_date=datetime(2020, 9, 27), to_date=datetime(2020, 10, 4), finished_at=datetime(2020, 10, 12)),
            MockLoggerRecord(channel_id=1, from_date=datetime(2020, 10, 4), to_date=datetime(2020, 10, 11), finished_at=datetime(2020, 10, 12)),
            MockLoggerRecord(channel_id=1, from_date=datetime(2020, 10, 11), to_date=datetime(2020, 10, 18), finished_at=None),
        ]

        self.bot.db.logger.select.return_value = rows

        channel = MockTextChannel(id=1)
        latest = await self.cog.get_latest_finished_process(channel)

        self.assertEqual(latest, MockLoggerRecord(channel_id=1, from_date=datetime(2020, 10, 4), to_date=datetime(2020, 10, 11), finished_at=datetime(2020, 10, 12)))

    """
    async def test_get_next_week(self):
        guild = MockGuild(id=8, created_at=datetime(2020, 9, 13, 1, 10, 15))
        (from_date, to_date) = self.cog.get_next_week(guild, None)
        self.assertEqual(from_date, datetime(2020, 9, 13, 1, 10, 15))
        self.assertEqual(to_date, datetime(2020, 9, 20, 1, 10, 15))

        guild = MockGuild(id=8, created_at=datetime(2020, 9, 13, 1, 10, 15))
        process = {'from_date': datetime(2020, 9, 20, 21, 22, 25), 'to_date':  datetime(2020, 9, 27, 22, 22, 25)}
        (from_date, to_date) = self.cog.get_next_week(guild, process)
        self.assertEqual(from_date, datetime(2020, 9, 27, 22, 22, 25))
        self.assertEqual(to_date, datetime(2020, 10, 4, 22, 22, 25))


    @patch('bot.cogs.logger.Logger.try_to_backup_messages_in_nonempty_channel')
    async def test_backup_messages_new_week_first_time(self, mocked_backup_messages):
        guild = MockGuild(id=8, created_at=datetime(2020, 9, 12, 12, 28, 33))
        guild.text_channels = [MockTextChannel(id=9), MockTextChannel(id=10)]

        self.bot.db.logger.select.return_value = []

        still_behind = await self.cog.backup_new_week(guild)

        self.assertEqual(mocked_backup_messages.call_count, len(guild.text_channels))
        mocked_backup_messages.assert_has_calls([
            call(guild.text_channels[0], datetime(2020, 9, 12, 12, 28, 33), datetime(2020, 9, 19, 12, 28, 33)),
            call(guild.text_channels[1], datetime(2020, 9, 12, 12, 28, 33), datetime(2020, 9, 19, 12, 28, 33))
        ])
        self.assertTrue(still_behind) # assuming that you don't run this code with modified system time
                                      # that sets the time date to before 2020.9.12, then this test would fail

    async def test_backup_messages_in_channel(self):
        channel = MockTextChannel(id=9)

        authors = {
            'bob': MockMember(id=10, name="Bob", avatar_url="http://image.cz.jpg", created_at=datetime(2020, 9, 13, 10, 00, 00)),
            'joe': MockUser(id=13, name="Joe", avatar_url="http://spam.com/thumb.png", created_at=datetime(2010, 9, 13, 10, 00, 00))
        }

        messages = [
            MockMessage(id=11, channel=channel, author=authors['bob'], content='First message', created_at=datetime(2020, 9, 13, 12, 50, 42), edited_at=None),
            MockMessage(id=12, channel=channel, author=authors['bob'], content='Second message', created_at=datetime(2020, 9, 13, 12, 55, 42), edited_at=None),
            MockMessage(id=14, channel=channel, author=authors['joe'], content='IMAGE!!!', created_at=datetime(2020, 9, 14, 14, 10, 12), edited_at=None),
            MockMessage(id=16, channel=channel, author=authors['bob'], content='react please', created_at=datetime(2020, 9, 14, 14, 12, 10), edited_at=None),
            MockMessage(id=17, channel=channel, author=authors['joe'], content='Hello there, I am here to try :kek: and <:kekw:4586234> and ofc ⭐', created_at=datetime(2020, 9, 14, 14, 12, 10), edited_at=None),
        ]

        messages[2].attachments = [
            MockAttachment(id=15, filename="nsfw.gif", url="discord.com/10/13/14")
        ]

        messages[3].reactions = [
            MockReaction(message=messages[3], emoji=MockEmoji(id=1234, name="kek"), users=[authors['bob'], authors['joe']])
        ]

        channel.history.return_value = AsyncIterator(messages)

        await self.cog.backup_messages_in_nonempty_channel(channel, from_date=datetime(2020, 9, 10, 12, 50, 42), to_date=datetime(2020, 9, 17, 12, 50, 42))

        self.bot.db.members.insert.assert_called_once_with([
            (10, "Bob", "http://image.cz.jpg", datetime(2020, 9, 13, 10, 00, 00)),
            (10, "Bob", "http://image.cz.jpg", datetime(2020, 9, 13, 10, 00, 00)),
            (13, "Joe", "http://spam.com/thumb.png", datetime(2010, 9, 13, 10, 00, 00)),
            (10, "Bob", "http://image.cz.jpg", datetime(2020, 9, 13, 10, 00, 00)),
            (13, "Joe", "http://spam.com/thumb.png", datetime(2010, 9, 13, 10, 00, 00)),
        ])

        self.bot.db.messages.insert.assert_called_once_with([
            (9, 10, 11, 'First message', datetime(2020, 9, 13, 12, 50, 42), None),
            (9, 10, 12, 'Second message', datetime(2020, 9, 13, 12, 55, 42), None),
            (9, 13, 14, 'IMAGE!!!', datetime(2020, 9, 14, 14, 10, 12), None),
            (9, 10, 16, 'react please', datetime(2020, 9, 14, 14, 12, 10), None),
            (9, 13, 17, 'Hello there, I am here to try :kek: and <:kekw:4586234> and ofc ⭐', datetime(2020, 9, 14, 14, 12, 10), None)
        ])

        self.bot.db.attachments.insert.assert_called_once_with([
            (15, "nsfw.gif", "discord.com/10/13/14")
        ])

        self.bot.db.reactions.insert.assert_called_once_with([
            (16, 1234, [10, 13])
        ])

        #self.bot.db.emojis.insert.assert_called_once_with([
        #    (17, ":kek:", 1),
        #    (17, ":kekw:", 1),
        #    (17, demojize("⭐"), 1)
        #])
    """

    async def test_Collectable(self):
        async def prepare(attachments):
            return [(attachment.id, attachment.filename, attachment.url)
                    for attachment in attachments]

        prepare_fn = prepare
        insert_fn = AsyncMock()

        collectable = logger.Collectable(prepare_fn, insert_fn)

        attachments = [
            MockAttachment(id=10, filename="file.txt", url="aabb.com"),
            MockAttachment(id=11, filename="filee2.txt", url="say.com"),
            MockAttachment(id=12, filename="zipped.zip", url="hello.com")
        ]

        await collectable.add(attachments)
        await collectable.db_insert()

        insert_fn.assert_called_once_with([
            (10, "file.txt", "aabb.com"),
            (11, "filee2.txt", "say.com"),
            (12, "zipped.zip", "hello.com")
        ])