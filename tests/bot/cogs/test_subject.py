import unittest
from unittest.mock import call, patch, Mock, AsyncMock

from datetime import datetime

from bot.cogs import subject
from tests.mocks.discord import MockBot, MockContext, MockGuild, MockTextChannel, MockMessage, MockEmoji
from tests.mocks.database import MockDatabase, MockSubjectRecord, MockSubjectRegisteredRecord, MockSubjectServerRecord

class SubjectTests(unittest.IsolatedAsyncioTestCase):
    async def test_subject_add_less_then_ten_codes(self):
        bot = MockBot()
        cog = subject.Subject(bot=bot)

        for i in range(10 + 1):
            cog.add = AsyncMock(return_value=None)

            ctx = MockContext()
            subjects = [f"IB{xxx:0>3}" for xxx in range(i)]
            await cog._add.callback(cog, ctx, *subjects)

            cog.add.assert_has_calls([
                call(ctx, code) for code in subjects
            ])

    async def test_subject_add_too_many_codes(self):
        bot = MockBot()
        cog = subject.Subject(bot=bot)

        for i in range(11, 20):
            cog.add = AsyncMock(return_value=None)

            ctx = AsyncMock()
            subjects = [f"IB{xxx:0>3}" for xxx in range(i)]
            await cog._add.callback(cog, ctx, *subjects)

            self.assertEqual(ctx.send_embed.call_count, 1)
            self.assertEqual(cog.add.call_count, 0)

    async def test_in_subject_channel_wrong_room(self):
        bot = MockBot()
        cog = subject.Subject(bot=bot)

        #
        guild_config = Mock()
        guild_config.id = 8
        guild_config.channels.subject_registration = 10

        config = Mock()
        config.guilds = [guild_config]
        #

        channel = MockTextChannel(id=12)
        guild = MockGuild(id=8, text_channels=[channel])
        ctx = MockContext(guild=guild)

        with patch('bot.cogs.subject.Config', config):
            await cog._in_subject_channel(ctx)

        ctx.send_error.assert_called_once()

    async def test_in_subject_channel_non_existing_channel(self):
        bot = MockBot()
        cog = subject.Subject(bot=bot)

        #
        guild_config = Mock()
        guild_config.id = 8
        guild_config.channels.subject_registration = 10

        config = Mock()
        config.guilds = [guild_config]
        #

        guild = MockGuild(id=8, text_channels=[])
        ctx = MockContext(guild=guild)

        with patch('bot.cogs.subject.Config', config):
            await cog._in_subject_channel(ctx)

        ctx.send_error.assert_called_once()



    async def test_subject_remove_less_then_ten_codes(self):
        bot = MockBot()
        cog = subject.Subject(bot=bot)

        for i in range(10 + 1):
            cog.remove = AsyncMock(return_value=None)

            ctx = MockContext()
            subjects = [f"IB{xxx:0>3}" for xxx in range(i)]
            await cog._remove.callback(cog, ctx, *subjects)

            cog.remove.assert_has_calls([
                call(ctx, code) for code in subjects
            ])

    async def test_subject_remove_too_many_codes(self):
        bot = MockBot()
        cog = subject.Subject(bot=bot)

        for i in range(11, 20):
            cog.remove = AsyncMock(return_value=None)

            ctx = AsyncMock()
            subjects = [f"IB{xxx:0>3}" for xxx in range(i)]
            await cog._remove.callback(cog, ctx, *subjects)

            self.assertEqual(ctx.send_embed.call_count, 1)
            self.assertEqual(cog.remove.call_count, 0)

    async def test_find_subject_not_found(self):
        bot = MockBot()
        bot.db = MockDatabase()
        cog = subject.Subject(bot=bot)

        subjects = []
        bot.db.subjects.find.return_value = subjects

        found_subject = await cog.find_subject(faculty="FI", code="IB002")
        self.assertEqual(found_subject, None)

    async def test_find_subject_found(self):
        bot = MockBot()
        bot.db = MockDatabase()
        cog = subject.Subject(bot=bot)

        subjects = [
            MockSubjectRecord(faculty="FI", code="IB000", name="MZI", url="muni/fi/ib/000", terms=["jaro 2020"], created_at=datetime(2020, 10, 11)),
        ]
        bot.db.subjects.find.return_value = subjects

        found_subject = await cog.find_subject(faculty="FI", code="IB000")
        self.assertEqual(found_subject, subjects[0])

    async def test_should_create_channel_already_exists(self):
        bot = MockBot()
        bot.db = MockDatabase()
        cog = subject.Subject(bot=bot)

        subject_record = MockSubjectRecord(faculty="FI", code="IB000", name="MZI", url="muni/fi/ib/000", terms=["jaro 2020"], created_at=datetime(2020, 10, 11))

        bot.db.subjects.find_registered.return_value = MockSubjectRegisteredRecord(faculty="FI", code="IB000", guild_id=8, member_ids=[11, 12, 13])
        bot.db.subjects.find_serverinfo.return_value = MockSubjectServerRecord(faculty="FI", code="IB000", guild_id=8, category_id=9, channel_id=10, voice_channel_id=None)
        ctx = MockContext(guild=MockGuild(id=8))

        should = await cog.should_create_channel(ctx, subject_record)
        self.assertFalse(should)

    async def test_should_create_channel_doesnt_exist_and_not_enough_users(self):
        guild_config = Mock()
        guild_config.id = 8
        guild_config.NEEDED_REACTIONS = 10

        config = Mock()
        config.guilds = [guild_config]

        with patch('bot.cogs.subject.Config', config):
            bot = MockBot()
            bot.db = MockDatabase()
            cog = subject.Subject(bot=bot)

            subject_record = MockSubjectRecord(faculty="FI", code="IB000", name="MZI", url="muni/fi/ib/000", terms=["jaro 2020"], created_at=datetime(2020, 10, 11))

            bot.db.subjects.find_registered.return_value = MockSubjectRegisteredRecord(faculty="FI", code="IB000", guild_id=8, member_ids=[11, 12, 13])
            bot.db.subjects.find_serverinfo.return_value = None
            ctx = MockContext(guild=MockGuild(id=8))

            should = await cog.should_create_channel(ctx, subject_record)
            self.assertFalse(should)

    async def test_should_create_channel_doesnt_exist_and_enough_users(self):
        guild_config = Mock()
        guild_config.id = 8
        guild_config.NEEDED_REACTIONS = 10

        config = Mock()
        config.guilds = [guild_config]

        with patch('bot.cogs.subject.Config', config):
            bot = MockBot()
            bot.db = MockDatabase()
            cog = subject.Subject(bot=bot)

            subject_record = MockSubjectRecord(faculty="FI", code="IB000", name="MZI", url="muni/fi/ib/000", terms=["jaro 2020"], created_at=datetime(2020, 10, 11))

            bot.db.subjects.find_registered.return_value = MockSubjectRegisteredRecord(faculty="FI", code="IB000", guild_id=8, member_ids=[11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
            bot.db.subjects.find_serverinfo.return_value = None
            ctx = MockContext(guild=MockGuild(id=8))

            should = await cog.should_create_channel(ctx, subject_record)
            self.assertTrue(should)


