import unittest
import unittest.mock
from datetime import datetime

import inject
from freezegun import freeze_time
from pytz import UTC

import bot.db
from bot.cogs.logger.message_iterator import MessageIterator
import tests.helpers as helpers


class MessageIteratorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.channel = helpers.MockTextChannel(id=10, created_at=datetime(2020, 10, 1, 12, 22))
        self.logger_repository = unittest.mock.AsyncMock()

    async def test_get_from_date_given_new_channel_returns_created_at_date(self) -> None:
        self.logger_repository.find_last_process.return_value = None
        self._mock_injections()

        iterator = MessageIterator(self.channel)
        date = await iterator._get_from_date()

        self.assertEqual(datetime(2020, 10, 1, 12, 22), date)

    async def test_get_from_date_given_existing_channel_returns(self) -> None:
        self.logger_repository.find_last_process.return_value = {
            'to_date': datetime(2020, 10, 7, 12, 22),
            'finished_at': datetime(2022, 10, 1, 12, 22, tzinfo=UTC)
        }
        self._mock_injections()

        iterator = MessageIterator(self.channel)
        date = await iterator._get_from_date()

        self.assertEqual(datetime(2020, 10, 7, 12, 22), date)

    async def test_get_from_date_given_existing_channel_and_finished_at_None_reruns(self) -> None:
        self.logger_repository.find_last_process.return_value = {
            'from_date': datetime(2020, 10, 1, 12, 22),
            'finished_at': None
        }
        self._mock_injections()

        iterator = MessageIterator(self.channel)
        date = await iterator._get_from_date()

        self.assertEqual(datetime(2020, 10, 1, 12, 22), date)

    @freeze_time(datetime(2022, 10, 2, 12, 22))
    async def test_history_given_calculates_weekly_range(self) -> None:
        self.logger_repository.find_last_process = unittest.mock.AsyncMock(return_value={
            'to_date': datetime(2020, 10, 1, 12, 22, tzinfo=UTC),
            'finished_at': datetime(2022, 10, 1, 12, 22, tzinfo=UTC)
        })
        self._mock_injections()

        iterator = MessageIterator(self.channel)
        await iterator.history()

        self.channel.history.assert_has_calls([
            unittest.mock.call(after=datetime(2020, 10, 1, 12, 22, tzinfo=UTC), before=datetime(2020, 10, 8, 12, 22, tzinfo=UTC), limit=None)
        ])

    @freeze_time(datetime(2020, 10, 2, 12, 22))
    async def test_history_given_task_finished_today_does_not_backup_future(self) -> None:
        self.logger_repository.find_last_process.return_value = {
            'to_date': datetime(2020, 10, 1, 12, 22, tzinfo=UTC),
            'finished_at': datetime(2020, 10, 2, 12, 22, tzinfo=UTC)
        }
        self._mock_injections()

        iterator = MessageIterator(self.channel)
        await iterator.history()

        self.channel.history.assert_has_calls([
            unittest.mock.call(after=datetime(2020, 10, 1, 12, 22, tzinfo=UTC), before=datetime(2020, 10, 2, 12, 22, tzinfo=UTC), limit=None)
        ])

    def _mock_injections(self):
        def setup_injections(binder: inject.Binder) -> None:
            binder.bind(bot.db.LoggerRepository, self.logger_repository)
        inject.clear_and_configure(setup_injections)
