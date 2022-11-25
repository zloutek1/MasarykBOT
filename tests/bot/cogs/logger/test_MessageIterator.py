import unittest
import unittest.mock
from datetime import datetime

import inject
from freezegun import freeze_time

import bot.db
import tests.helpers as helpers
from bot.db.logger import ProcessContext
from cogs.logger.MessageIterator import MessageIterator


class LoggerTests(unittest.IsolatedAsyncioTestCase):
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
        self.logger_repository.find_last_process.return_value = {'to_date': datetime(2020, 10, 7, 12, 22)}
        self._mock_injections()

        iterator = MessageIterator(self.channel)
        date = await iterator._get_from_date()

        self.assertEqual(datetime(2020, 10, 7, 12, 22), date)

    async def test_history_given_calculates_weekly_range(self) -> None:
        self.logger_repository.find_last_process = unittest.mock.AsyncMock(return_value={'to_date': datetime(2020, 10, 1, 12, 22)})
        self.logger_repository.with_process = lambda data: ProcessContext(self.logger_repository, data)
        self._mock_injections()

        iterator = MessageIterator(self.channel)
        await iterator.history()

        self.channel.history.assert_has_calls([
            unittest.mock.call(after=datetime(2020, 10, 1, 12, 22), before=datetime(2020, 10, 8, 12, 22), limit=None)
        ])

    @freeze_time(datetime(2020, 10, 2, 12, 22))
    async def test_history_given_task_finished_today_does_not_backup_future(self) -> None:
        self.logger_repository.find_last_process.return_value = {'to_date': datetime(2020, 10, 1, 12, 22)}
        self.logger_repository.with_process = lambda data: ProcessContext(self.logger_repository, data)
        self._mock_injections()

        iterator = MessageIterator(self.channel)
        await iterator.history()

        self.channel.history.assert_has_calls([
            unittest.mock.call(after=datetime(2020, 10, 1, 12, 22), before=datetime(2020, 10, 2, 12, 22), limit=None)
        ])

    def _mock_injections(self):
        def setup_injections(binder: inject.Binder) -> None:
            binder.bind(bot.db.LoggerRepository, self.logger_repository)
        inject.clear_and_configure(setup_injections)
