import unittest
import unittest.mock
from datetime import datetime

import inject
from discord.utils import time_snowflake
from freezegun import freeze_time
from pytz import UTC

import bot.db
from bot.cogs.logger.message_iterator import MessageIterator
import tests.helpers as helpers
from bot.db import LoggerEntity


class MessageIteratorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.channel = helpers.MockTextChannel(id=10, created_at=datetime(2020, 10, 1, 12, 22, tzinfo=UTC))
        self.channel.last_message_id = time_snowflake(datetime(2022, 10, 1, 12, 22, tzinfo=UTC))
        self.logger_repository = unittest.mock.AsyncMock()

    async def test_get_next_from_date_given_new_channel_returns_created_at_date(self) -> None:
        self.logger_repository.find_last_process.return_value = None
        self._mock_injections()

        iterator = MessageIterator(self.channel)
        date = await iterator._get_next_from_date()

        self.assertEqual(datetime(2020, 10, 1, 12, 22, tzinfo=UTC), date)

    async def test_get_next_from_date_given_existing_channel_returns(self) -> None:
        self.logger_repository.find_last_process.return_value = LoggerEntity(
            1,
            datetime(2020, 10, 7, 12, 22, tzinfo=UTC),
            datetime(2022, 10, 1, 12, 22, tzinfo=UTC)
        )
        self._mock_injections()

        iterator = MessageIterator(self.channel)
        date = await iterator._get_next_from_date()

        self.assertEqual(datetime(2020, 10, 7, 12, 22, tzinfo=UTC), date)

    async def test_get_next_from_date_given_existing_channel_and_finished_at_None_reruns(self) -> None:
        self.logger_repository.find_last_process.return_value = LoggerEntity(
            1,
            datetime(2020, 10, 1, 12, 22, tzinfo=UTC),
            None,
            None
        )
        self._mock_injections()

        iterator = MessageIterator(self.channel)
        date = await iterator._get_next_from_date()

        self.assertEqual(datetime(2020, 10, 1, 12, 22, tzinfo=UTC), date)

    @freeze_time(datetime(2022, 10, 12, 11, 30, tzinfo=UTC))
    async def test_history_given_finished_process_loads_next_1000(self) -> None:
        self.logger_repository.find_last_process.return_value = LoggerEntity(
            1,
            datetime(2020, 9, 1, 9, 22, tzinfo=UTC),
            datetime(2020, 9, 25, 9, 22, tzinfo=UTC),
            datetime(2022, 10, 12, 11, 30, tzinfo=UTC),
        )
        self._mock_injections()

        iterator = MessageIterator(self.channel)
        await iterator.history()

        self.channel.history.assert_has_calls([
            unittest.mock.call(after=datetime(2020, 9, 25, 9, 22, tzinfo=UTC), limit=1_000)
        ])

    @freeze_time(datetime(2020, 10, 2, 12, 22, tzinfo=UTC))
    async def test_history_given_task_finished_today_does_not_backup_future(self) -> None:
        self.logger_repository.find_last_process.return_value = LoggerEntity(
            1,
            datetime(2020, 10, 1, 12, 22, tzinfo=UTC),
            datetime(2020, 10, 2, 12, 22, tzinfo=UTC)
        )
        self._mock_injections()

        iterator = MessageIterator(self.channel)
        await iterator.history()

        self.channel.history.assert_not_called()

    def _mock_injections(self) -> None:
        def setup_injections(binder: inject.Binder) -> None:
            binder.bind(bot.db.LoggerRepository, self.logger_repository)

        inject.clear_and_configure(setup_injections)
