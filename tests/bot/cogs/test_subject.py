import unittest
from unittest.mock import call

from datetime import datetime

from bot.cogs import subject
from tests.mocks.discord import MockBot, MockContext, MockGuild, MockMessage, MockEmoji
from tests.mocks.database import MockDatabase, MockSubjectRecord

class SubjectTests(unittest.IsolatedAsyncioTestCase):
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

