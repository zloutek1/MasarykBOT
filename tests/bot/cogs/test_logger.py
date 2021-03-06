import unittest
from unittest.mock import patch, call, MagicMock, AsyncMock

from emoji import demojize
from datetime import datetime, date
from collections import deque

from bot.cogs.utils import db
from bot.cogs import logger

from tests.mocks.discord import (MockBot,
                                MockRole, MockMember, MockUser,
                                MockGuild, MockCategoryChannel, MockTextChannel,
                                MockMessage, MockAttachment, MockReaction, MockEmoji,
                                AsyncIterator)
from tests.mocks.database import MockDatabase, MockLoggerRecord
from tests.mocks.helpers import MockReturnFunc


class LoggerBackupUntilPresentTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = MockBot()
        self.bot.db = MockDatabase()
        self.cog = logger.Logger(bot=self.bot)

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
            call(channel, datetime(2020, 9, 20), datetime(2020, 9, 27), False),
            call(channel, datetime(2020, 10, 4), datetime(2020, 10, 11), False)
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

    async def test_get_next_week_channel_beginning(self):
        channel = MockTextChannel(id=11, created_at=datetime(2020, 9, 13))
        process = None

        from_date, to_date = self.cog.get_next_week(channel, process)
        self.assertEqual(from_date, datetime(2020, 9, 13))
        self.assertEqual(to_date, datetime(2020, 9, 20))

    async def test_get_next_week_process(self):
        channel = MockTextChannel(id=11, created_at=datetime(2020, 9, 13))
        process = MockLoggerRecord(channel_id=1, from_date=datetime(2020, 9, 20), to_date=datetime(2020, 9, 27), finished_at=None)

        from_date, to_date = self.cog.get_next_week(channel, process)
        self.assertEqual(from_date, datetime(2020, 9, 27))
        self.assertEqual(to_date, datetime(2020, 10, 4))

    async def test_get_next_week_current_week(self):
        channel = MockTextChannel(id=11, created_at=datetime(2020, 9, 13))
        process = MockLoggerRecord(channel_id=1, from_date=datetime(2020, 9, 27), to_date=datetime(2020, 10, 4), finished_at=None)

        with patch('bot.cogs.logger.datetime') as mocked_datetime:
            mocked_datetime.now.return_value = datetime(2020, 9, 27)

            from_date, to_date = self.cog.get_next_week(channel, process)
            self.assertEqual(from_date, datetime(2020, 9, 26))
            self.assertEqual(to_date, datetime(2020, 10, 4))


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

        emojis = [
            MockEmoji(id=1234, name="kek", url="https://cdn.discordapp.com/emojis/1234.png", animated=False)
        ]

        messages[3].reactions = [
            MockReaction(message=messages[3], emoji=emojis[0], users=[authors['bob'], authors['joe']])
        ]

        self.bot.db.logger.process =  MagicMock()
        channel.history.return_value = AsyncIterator(messages)

        await self.cog.backup_in_range(channel, from_date=datetime(2020, 9, 10, 12, 50, 42), to_date=datetime(2020, 9, 17, 12, 50, 42), is_first_week=False)

        self.bot.db.members.insert.assert_called_once_with([
            (10, "Bob", "http://image.cz.jpg", datetime(2020, 9, 13, 10, 00, 00)),
            (10, "Bob", "http://image.cz.jpg", datetime(2020, 9, 13, 10, 00, 00)),
            (13, "Joe", "http://spam.com/thumb.png", datetime(2010, 9, 13, 10, 00, 00)),
            (10, "Bob", "http://image.cz.jpg", datetime(2020, 9, 13, 10, 00, 00)),
            (13, "Joe", "http://spam.com/thumb.png", datetime(2010, 9, 13, 10, 00, 00)),
        ])

        self.bot.db.messages.insert.assert_called_once_with([
            (9, 10, 11, 'First message', datetime(2020, 9, 13, 12, 50, 42)),
            (9, 10, 12, 'Second message', datetime(2020, 9, 13, 12, 55, 42)),
            (9, 13, 14, 'IMAGE!!!', datetime(2020, 9, 14, 14, 10, 12)),
            (9, 10, 16, 'react please', datetime(2020, 9, 14, 14, 12, 10)),
            (9, 13, 17, 'Hello there, I am here to try :kek: and <:kekw:4586234> and ofc ⭐', datetime(2020, 9, 14, 14, 12, 10))
        ])

        self.bot.db.attachments.insert.assert_called_once_with([
            (14, 15, "nsfw.gif", "discord.com/10/13/14")
        ])

        self.bot.db.reactions.insert.assert_called_once_with([
            (16, 1234, [10, 13], datetime(2020, 9, 14, 14, 12, 10))
        ])

        self.bot.db.emojis.insert.assert_called_once_with([
            (1234, "kek", "https://cdn.discordapp.com/emojis/1234.png", False),
            (4586234, "kekw", "https://cdn.discordapp.com/emojis/4586234.png", False),
            (0x2B50, demojize("⭐").strip(":"), "https://unicode.org/emoji/charts/full-emoji-list.html#2b50", False)
        ])

        self.bot.db.message_emojis.insert.assert_called_once_with([
            (17, 4586234, 1),
            (17, 0x2B50, 1)
        ])

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



class LoggerBackupOnEventsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = MockBot()
        self.bot.db = MockDatabase()
        self.cog = logger.Logger(bot=self.bot)

    async def _test_on_event(self, args, queues, event_fn, put_fn, *, expected):
        """
        Generified test for on_guild_create, on_message, ... events
        """
        await event_fn(*args)
        self.assertIn(put_fn, queues)
        self.assertEqual(queues[put_fn], expected)

    async def test_task_put_queues_to_database(self):
        self.cog.insert_queues = {
            AsyncMock(): deque(list(range(5432))),
            AsyncMock(): deque("a" * 1200)
        }
        self.update_queues = {
            AsyncMock(): deque(list(range(8000))),
            AsyncMock(): deque(['a', 1, 4] * 800)
        }
        self.delete_queues = {
            AsyncMock(): deque([AsyncMock() for _ in range(1234)])
        }

        self.cog.put_queues_to_database = AsyncMock()
        await self.cog.task_put_queues_to_database.coro(self.cog)

        self.cog.put_queues_to_database.assert_has_calls([
            call(self.cog.insert_queues, limit=1000),
            call(self.cog.update_queues, limit=2000),
            call(self.cog.delete_queues, limit=1000)
        ])

    async def test_put_queues_to_database(self):
        fn1 = AsyncMock()
        fn2 = AsyncMock()

        queues = {
            fn1: deque([1, 2, 3]),
            fn2: deque(['a', 1, 4])
        }

        self.cog.put_queue_to_database = AsyncMock()
        await self.cog.put_queues_to_database(queues, limit=1000)

        self.cog.put_queue_to_database.assert_has_calls([
            call(fn1, deque([1, 2, 3]), limit=1000),
            call(fn2, deque(['a', 1, 4]), limit=1000)
        ])

    async def test_put_queue_to_database(self):
        insert_number_fn = AsyncMock()
        insert_number_fn.__qualname__ = "insert_number_fn"

        insert_str_fn = AsyncMock()
        insert_str_fn.__qualname__ = "insert_number_fn"

        queue = deque([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
        await self.cog.put_queue_to_database(insert_number_fn, queue, limit=10)
        insert_number_fn.assert_called_once_with([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

        queue = deque(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k'])
        await self.cog.put_queue_to_database(insert_str_fn, queue, limit=10)
        insert_str_fn.assert_called_once_with(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j'])

    """
    async def test_on_events(self):
        async def test_on_insert(item, event_fn, put_fn):
            await event_fn(item)
            self.assertIn(put_fn, self.cog.insert_queues)
            self.assertEqual(self.cog.insert_queues[put_fn], expected)


        async def test_on_update(new_item, event_fn, put_fn):
            await event_fn(AsyncMock(), new_item)
            self.assertIn(put_fn, self.cog.update_queues)
            self.assertEqual(self.cog.update_queues[put_fn], expected)


        async def test_on_delete(item, event_fn, put_fn):
            expected = deque([(item.id,)])
            await event_fn(item)
            self.assertIn(put_fn, self.cog.delete_queues)
            self.assertEqual(self.cog.delete_queues[put_fn], expected)

        expected = deque([(1, 2, 3)])
        for attr in vars(self.bot.db).values():
            if isinstance(attr, db.Mapper):
                attr.prepare_one = AsyncMock(return_value=(1, 2, 3))

        await test_on_insert(MockGuild(), self.cog.on_guild_join, self.bot.db.guilds.insert)
        await test_on_update(MockGuild(), self.cog.on_guild_update, self.bot.db.guilds.update)
        await test_on_delete(MockGuild(), self.cog.on_guild_remove, self.bot.db.guilds.soft_delete)

        await test_on_insert(MockTextChannel(), self.cog.on_textchannel_create, self.bot.db.channels.insert)
        await test_on_update(MockTextChannel(), self.cog.on_textchannel_update, self.bot.db.channels.update)
        await test_on_delete(MockTextChannel(), self.cog.on_textchannel_delete, self.bot.db.channels.soft_delete)

        await test_on_insert(MockCategoryChannel(), self.cog.on_category_create, self.bot.db.categories.insert)
        await test_on_update(MockCategoryChannel(), self.cog.on_category_update, self.bot.db.categories.update)
        await test_on_delete(MockCategoryChannel(), self.cog.on_category_delete, self.bot.db.categories.soft_delete)

        await test_on_insert(MockMessage(), self.cog.on_message, self.bot.db.messages.insert)
        await test_on_update(MockMessage(), self.cog.on_message_edit, self.bot.db.messages.update)
        await test_on_delete(MockMessage(), self.cog.on_message_delete, self.bot.db.messages.soft_delete)

        #await test_on_insert(MockReaction(), self.cog.on_reaction_add, self.bot.db.reactions.insert)

        await test_on_insert(MockMember(), self.cog.on_member_join, self.bot.db.members.insert)
        await test_on_update(MockMember(), self.cog.on_member_update, self.bot.db.members.update)
        await test_on_delete(MockMember(), self.cog.on_member_remove, self.bot.db.members.soft_delete)

        await test_on_insert(MockRole(), self.cog.on_guild_role_create, self.bot.db.roles.insert)
        await test_on_update(MockRole(), self.cog.on_guild_role_update, self.bot.db.roles.update)
        await test_on_delete(MockRole(), self.cog.on_guild_role_remove, self.bot.db.roles.soft_delete)
    """

    async def test_on_guild_join(self):
        args = [MockGuild()]
        self.bot.db.guilds.prepare_one = AsyncMock(return_value=(1, 2, 3))
        expected = deque([(1, 2, 3)])
        await self._test_on_event(args=args, queues=self.cog.insert_queues, event_fn=self.cog.on_guild_join, put_fn=self.bot.db.guilds.insert, expected=expected)

    async def test_on_guild_update(self):
        args = [MockGuild(), MockGuild()]
        self.bot.db.guilds.prepare_one = AsyncMock(return_value=(1, 2, 3))
        expected = deque([(1, 2, 3)])
        await self._test_on_event(args=args, queues=self.cog.update_queues, event_fn=self.cog.on_guild_update, put_fn=self.bot.db.guilds.update, expected=expected)

    async def test_on_guild_remove(self):
        args = [MockGuild(id=123)]
        expected = deque([(123,)])
        await self._test_on_event(args=args, queues=self.cog.delete_queues, event_fn=self.cog.on_guild_remove, put_fn=self.bot.db.guilds.soft_delete, expected=expected)


    async def test_on_textchannel_create(self):
        args = [MockTextChannel()]
        self.bot.db.channels.prepare_one = AsyncMock(return_value=(1, 2, 3))
        expected = deque([(1, 2, 3)])
        await self._test_on_event(args=args, queues=self.cog.insert_queues, event_fn=self.cog.on_textchannel_create, put_fn=self.bot.db.channels.insert, expected=expected)

    async def test_on_textchannel_update(self):
        args = [MockTextChannel(), MockTextChannel()]
        self.bot.db.channels.prepare_one = AsyncMock(return_value=(1, 2, 3))
        expected = deque([(1, 2, 3)])
        await self._test_on_event(args=args, queues=self.cog.update_queues, event_fn=self.cog.on_textchannel_update, put_fn=self.bot.db.channels.update, expected=expected)

    async def test_on_textchannel_delete(self):
        args = [MockTextChannel(id=123)]
        expected = deque([(123,)])
        await self._test_on_event(args=args, queues=self.cog.delete_queues, event_fn=self.cog.on_textchannel_delete, put_fn=self.bot.db.channels.soft_delete, expected=expected)

    async def test_on_category_create(self):
        args = [MockCategoryChannel()]
        self.bot.db.categories.prepare_one = AsyncMock(return_value=(1, 2, 3))
        expected = deque([(1, 2, 3)])
        await self._test_on_event(args=args, queues=self.cog.insert_queues, event_fn=self.cog.on_category_create, put_fn=self.bot.db.categories.insert, expected=expected)

    async def test_on_category_update(self):
        args = [MockCategoryChannel(), MockCategoryChannel()]
        self.bot.db.categories.prepare_one = AsyncMock(return_value=(1, 2, 3))
        expected = deque([(1, 2, 3)])
        await self._test_on_event(args=args, queues=self.cog.update_queues, event_fn=self.cog.on_category_update, put_fn=self.bot.db.categories.update, expected=expected)

    async def test_on_category_delete(self):
        args = [MockCategoryChannel(id=123)]
        expected = deque([(123,)])
        await self._test_on_event(args=args, queues=self.cog.delete_queues, event_fn=self.cog.on_category_delete, put_fn=self.bot.db.categories.soft_delete, expected=expected)

    async def test_on_message(self):
        args = [MockMessage(content="hello")]
        self.bot.db.messages.prepare_one = AsyncMock(return_value=(1, 2, 3))
        expected = deque([(1, 2, 3)])
        await self._test_on_event(args=args, queues=self.cog.insert_queues, event_fn=self.cog.on_message, put_fn=self.bot.db.messages.insert, expected=expected)

    async def test_on_message_edit(self):
        args = [MockMessage(), MockMessage(content="hello")]
        self.bot.db.messages.prepare_one = AsyncMock(return_value=(1, 2, 3))
        expected = deque([(1, 2, 3)])
        await self._test_on_event(args=args, queues=self.cog.update_queues, event_fn=self.cog.on_message_edit, put_fn=self.bot.db.messages.update, expected=expected)

    async def test_on_message_delete(self):
        args = [MockMessage(id=213)]
        expected = deque([(213,)])
        await self._test_on_event(args=args, queues=self.cog.delete_queues, event_fn=self.cog.on_message_delete, put_fn=self.bot.db.messages.soft_delete, expected=expected)

    async def test_on_reaction_add(self):
        args = [MockReaction(), MockUser()]
        self.bot.db.reactions.prepare_one = AsyncMock(return_value=(1, 2, 3))
        expected = deque([(1, 2, 3)])
        await self._test_on_event(args=args, queues=self.cog.insert_queues, event_fn=self.cog.on_reaction_add, put_fn=self.bot.db.reactions.insert, expected=expected)

    async def test_on_member_join(self):
        args = [MockMember()]
        self.bot.db.members.prepare_one = AsyncMock(return_value=(1, 2, 3))
        expected = deque([(1, 2, 3)])
        await self._test_on_event(args=args, queues=self.cog.insert_queues, event_fn=self.cog.on_member_join, put_fn=self.bot.db.members.insert, expected=expected)

    async def test_on_member_update(self):
        args = [MockMember(), MockMember()]
        self.bot.db.members.prepare_one = AsyncMock(return_value=(1, 2, 3))
        expected = deque([(1, 2, 3)])
        await self._test_on_event(args=args, queues=self.cog.update_queues, event_fn=self.cog.on_member_update, put_fn=self.bot.db.members.update, expected=expected)

    async def test_on_member_remove(self):
        args = [MockMember(id=123)]
        expected = deque([(123,)])
        await self._test_on_event(args=args, queues=self.cog.delete_queues, event_fn=self.cog.on_member_remove, put_fn=self.bot.db.members.soft_delete, expected=expected)

    async def test_on_guild_role_create(self):
        args = [MockRole()]
        self.bot.db.roles.prepare_one = AsyncMock(return_value=(1, 2, 3))
        expected = deque([(1, 2, 3)])
        await self._test_on_event(args=args, queues=self.cog.insert_queues, event_fn=self.cog.on_guild_role_create, put_fn=self.bot.db.roles.insert, expected=expected)

    async def test_on_guild_role_update(self):
        args = [MockRole(), MockRole()]
        self.bot.db.roles.prepare_one = AsyncMock(return_value=(1, 2, 3))
        expected = deque([(1, 2, 3)])
        await self._test_on_event(args=args, queues=self.cog.update_queues, event_fn=self.cog.on_guild_role_update, put_fn=self.bot.db.roles.update, expected=expected)

    async def test_on_guild_role_remove(self):
        args = [MockRole(id=123)]
        expected = deque([(123,)])
        await self._test_on_event(args=args, queues=self.cog.delete_queues, event_fn=self.cog.on_guild_role_remove, put_fn=self.bot.db.roles.soft_delete, expected=expected)


