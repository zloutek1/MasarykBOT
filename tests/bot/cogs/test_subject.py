import unittest
from unittest.mock import call, patch, Mock, AsyncMock

from datetime import datetime

from bot.cogs import subject
from tests.mocks.discord import MockBot, MockContext, MockGuild, MockTextChannel, MockCategoryChannel, MockMessage, MockEmoji
from tests.mocks.database import MockDatabase, MockSubjectRecord, MockSubjectRegisteredRecord, MockSubjectServerRecord

class SubjectTests(unittest.IsolatedAsyncioTestCase):
    async def test_subject_add_less_then_ten_codes(self):
        bot = MockBot()
        cog = subject.Subject(bot=bot)

        for i in range(10 + 1):
            cog.add_subject = AsyncMock(return_value=None)

            ctx = MockContext()
            subjects = [f"IB{xxx:0>3}" for xxx in range(i)]
            await cog.add.callback(cog, ctx, *subjects)

            cog.add_subject.assert_has_calls([
                call(ctx, code) for code in subjects
            ])

    async def test_subject_add_too_many_codes(self):
        bot = MockBot()
        cog = subject.Subject(bot=bot)

        for i in range(11, 20):
            cog.add_subject = AsyncMock(return_value=None)

            ctx = AsyncMock()
            subjects = [f"IB{xxx:0>3}" for xxx in range(i)]
            await cog.add.callback(cog, ctx, *subjects)

            self.assertEqual(ctx.send_embed.call_count, 1)
            self.assertEqual(cog.add_subject.call_count, 0)

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

        channel1 = MockTextChannel(id=10)
        channel2 = MockTextChannel(id=11)
        guild = MockGuild(id=8, text_channels=[channel1, channel2])
        ctx = MockContext(guild=guild, channel=channel2)

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

    async def test_pattern_to_faculty_code(self):
        bot = MockBot()
        cog = subject.Subject(bot=bot)

        self.assertEqual(cog.pattern_to_faculty_code("FI:IB000"), ("FI", "IB000"))
        self.assertEqual(cog.pattern_to_faculty_code("IB000"), ("FI", "IB000"))
        self.assertEqual(cog.pattern_to_faculty_code("FF:IB000"), ("FF", "IB000"))
        self.assertEqual(cog.pattern_to_faculty_code("FI:IB0%"), ("FI", "IB0%"))
        self.assertEqual(cog.pattern_to_faculty_code("a:a:a:a"), ("a", "a:a:a"))

    async def test_subject_remove_less_then_ten_codes(self):
        bot = MockBot()
        cog = subject.Subject(bot=bot)

        for i in range(10 + 1):
            cog.remove_subject = AsyncMock(return_value=None)

            ctx = MockContext()
            subjects = [f"IB{xxx:0>3}" for xxx in range(i)]
            await cog.remove.callback(cog, ctx, *subjects)

            cog.remove_subject.assert_has_calls([
                call(ctx, code) for code in subjects
            ])

    async def test_subject_remove_too_many_codes(self):
        bot = MockBot()
        cog = subject.Subject(bot=bot)

        for i in range(11, 20):
            cog.remove_subject = AsyncMock(return_value=None)

            ctx = AsyncMock()
            subjects = [f"IB{xxx:0>3}" for xxx in range(i)]
            await cog.remove.callback(cog, ctx, *subjects)

            self.assertEqual(ctx.send_embed.call_count, 1)
            self.assertEqual(cog.remove_subject.call_count, 0)

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

    async def test_try_to_get_existing_channel(self):
        bot = MockBot()
        bot.db.subjects.set_channel = AsyncMock(return_value=None)
        cog = subject.Subject(bot=bot)

        categories = [
            MockCategoryChannel(id=3, name="IBXXX", position=0),
            MockCategoryChannel(id=5, name="PVXXX", position=1)
        ]
        text_channels = [
            MockTextChannel(id=2, name="IB000", category=categories[0], position=0),
            MockTextChannel(id=4, name="IB002", category=categories[0], position=1),
            MockTextChannel(id=6, name="PV102", category=categories[1], position=0)
        ]
        guild = MockGuild(id=1, text_channels=text_channels, categories=categories)
        ctx = MockContext(guild=guild)

        subject_record = MockSubjectRecord(faculty="FI", code="IB000", name="MZI Of Ab", url="muni/fi/ib/000", terms=["jaro 2020"], created_at=datetime(2020, 10, 11))
        actual = await cog.try_to_get_existing_channel(ctx, subject_record)
        self.assertEqual(actual, text_channels[0])

    async def test_try_to_get_existing_channel_exactly(self):
        bot = MockBot()
        bot.db.subjects.set_channel = AsyncMock(return_value=None)
        cog = subject.Subject(bot=bot)

        categories = [
            MockCategoryChannel(id=3, name="IBXXX", position=0),
            MockCategoryChannel(id=5, name="PVXXX", position=1)
        ]
        text_channels = [
            MockTextChannel(id=1, name="IB000cv", category=categories[0], position=0),
            MockTextChannel(id=2, name="IB000", category=categories[0], position=0),
            MockTextChannel(id=4, name="IB002", category=categories[0], position=1),
            MockTextChannel(id=6, name="PV102", category=categories[1], position=0)
        ]
        guild = MockGuild(id=1, text_channels=text_channels, categories=categories)
        ctx = MockContext(guild=guild)

        subject_record = MockSubjectRecord(faculty="FI", code="IB000", name="MZI Of Ab", url="muni/fi/ib/000", terms=["jaro 2020"], created_at=datetime(2020, 10, 11))
        actual = await cog.try_to_get_existing_channel(ctx, subject_record)
        self.assertEqual(actual, text_channels[1])


    async def test_reorder_in_order(self):
        bot = MockBot()
        cog = subject.Subject(bot=bot)

        cog.is_subject_channel = AsyncMock(return_value=True)

        def side_effect(guild_id, code, faculty):
            return MockSubjectRecord(faculty, code, "", "", [], datetime.now(), None, None)

        bot.db.subjects.get_category = AsyncMock()
        bot.db.subjects.get_category.side_effect = side_effect

        categories = [
            MockCategoryChannel(id=3, name="IBXXX", position=0),
            MockCategoryChannel(id=5, name="PVXXX", position=1)
        ]
        text_channels = [
            MockTextChannel(id=2, name="IB000", category=categories[0], position=0),
            MockTextChannel(id=4, name="IB002", category=categories[0], position=1),
            MockTextChannel(id=6, name="PV102", category=categories[1], position=0)
        ]
        guild = MockGuild(id=1, text_channels=text_channels, categories=categories)

        ctx = MockContext(guild=guild)
        await cog.reorder.callback(cog, ctx)

        guild.create_category.assert_not_called()
        for channel in text_channels:
            channel.edit.assert_not_called()
        for category in categories:
            category.delete.assert_not_called()

    async def test_check_if_engough_users_signed_not_enough_users(self):
        bot = MockBot()
        bot.db.subjects.find_registered = AsyncMock(return_value=MockSubjectRegisteredRecord(faculty="FI", code="IB000", guild_id=8, member_ids=[11, 12, 13]))
        bot.db.subjects.find_serverinfo = AsyncMock(return_value=MockSubjectServerRecord(faculty="FI", code="IB000", guild_id=8, category_id=9, channel_id=10, voice_channel_id=None))

        #
        guild = Mock()
        guild.id = 8
        guild.NEEDED_REACTIONS = 10

        config = Mock()
        config.guilds = [guild]
        #

        guild_id = 8
        _subject = MockSubjectRecord(faculty="FI", code="IB000", name="MZI", url="muni/fi/ib/000", terms=["jaro 2020"], created_at=datetime(2020, 10, 11))

        cog = subject.Subject(bot=bot)
        with patch('bot.cogs.subject.Config', config):
            actual = await cog.check_if_engough_users_signed(guild_id, _subject)
            self.assertFalse(actual)

    async def test_check_if_engough_users_signed_enough_users(self):
        bot = MockBot()
        bot.db.subjects.find_registered = AsyncMock(return_value=MockSubjectRegisteredRecord(faculty="FI", code="IB000", guild_id=8, member_ids=[11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]))
        bot.db.subjects.find_serverinfo = AsyncMock(return_value=MockSubjectServerRecord(faculty="FI", code="IB000", guild_id=8, category_id=9, channel_id=10, voice_channel_id=None))

        #
        guild = Mock()
        guild.id = 8
        guild.NEEDED_REACTIONS = 10

        config = Mock()
        config.guilds = [guild]
        #

        guild_id = 8
        _subject = MockSubjectRecord(faculty="FI", code="IB000", name="MZI", url="muni/fi/ib/000", terms=["jaro 2020"], created_at=datetime(2020, 10, 11))

        cog = subject.Subject(bot=bot)
        with patch('bot.cogs.subject.Config', config):
            actual = await cog.check_if_engough_users_signed(guild_id, _subject)
            self.assertTrue(actual)

    async def test_subject_to_channel_name(self):
        bot = MockBot()
        cog = subject.Subject(bot=bot)

        ctx = MockContext()
        ctx.channel_name.side_effect = lambda name: name

        _subject = MockSubjectRecord(faculty="FI", code="IB000", name="MZI Of Ab", url="muni/fi/ib/000", terms=["jaro 2020"], created_at=datetime(2020, 10, 11))
        actual = cog.subject_to_channel_name(ctx, _subject)
        self.assertEqual(actual, "IB000 MZI Of Ab")

        _subject = MockSubjectRecord(faculty="FF", code="ABCDE", name="One of Two", url="muni/fi/ib/000", terms=["jaro 2020"], created_at=datetime(2020, 10, 11))
        actual = cog.subject_to_channel_name(ctx, _subject)
        self.assertEqual(actual, "FF:ABCDE One of Two")

    async def test_group_by_term(self):
        bot = MockBot()
        cog = subject.Subject(bot=bot)

        subjects = [
            MockSubjectRecord(faculty="FI", code="IB000", name="MZI Of Ab", url="muni/fi/ib/000", terms=["jaro 2020"], created_at=datetime(2020, 10, 11)),
            MockSubjectRecord(faculty="FI", code="IB000", name="MZI Of Ab", url="muni/fi/ib/000", terms=["podzim 2020"], created_at=datetime(2020, 10, 11)),
            MockSubjectRecord(faculty="FI", code="IB015", name="GHC Of XX", url="muni/fi/ib/015", terms=["jaro 2021"], created_at=datetime(2020, 10, 11)),
            MockSubjectRecord(faculty="FI", code="IB123", name="123XY", url="muni/fi/ib/123", terms=["podzim 2020"], created_at=datetime(2020, 10, 11)),
            MockSubjectRecord(faculty="FI", code="PV111", name="MZI Of Ab", url="muni/fi/pb/111", terms=["podzim 2020"], created_at=datetime(2020, 10, 11)),
            MockSubjectRecord(faculty="FF", code="ABCDE", name="MZI Of Ab", url="muni/ff/ab/cde", terms=["podzim 2020"], created_at=datetime(2020, 10, 11))
        ]

        expected = {
            'jaro 2020': [
                MockSubjectRecord(faculty="FI", code="IB000", name="MZI Of Ab", url="muni/fi/ib/000", terms=["jaro 2020"], created_at=datetime(2020, 10, 11))
            ],
            'podzim 2020': [
                MockSubjectRecord(faculty="FI", code="IB000", name="MZI Of Ab", url="muni/fi/ib/000", terms=["podzim 2020"], created_at=datetime(2020, 10, 11)),
                MockSubjectRecord(faculty="FI", code="IB123", name="123XY", url="muni/fi/ib/123", terms=["podzim 2020"], created_at=datetime(2020, 10, 11)),
                MockSubjectRecord(faculty="FI", code="PV111", name="MZI Of Ab", url="muni/fi/pb/111", terms=["podzim 2020"], created_at=datetime(2020, 10, 11)),
                MockSubjectRecord(faculty="FF", code="ABCDE", name="MZI Of Ab", url="muni/ff/ab/cde", terms=["podzim 2020"], created_at=datetime(2020, 10, 11))
            ],
            'jaro 2021': [
                MockSubjectRecord(faculty="FI", code="IB015", name="GHC Of XX", url="muni/fi/ib/015", terms=["jaro 2021"], created_at=datetime(2020, 10, 11)),
            ]
        }

        actual = cog.group_by_term(subjects)
        self.assertDictEqual(expected, actual)

