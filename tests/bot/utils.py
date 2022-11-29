import unittest.mock

import asyncpg
import inject

import bot.db



def mock_database(binder: inject.Binder) -> None:
    binder.bind(asyncpg.Pool, unittest.mock.MagicMock())

    for repository in bot.db.discord.REPOSITORIES:
        binder.bind(repository, unittest.mock.AsyncMock())

    for mapper in bot.db.discord.MAPPERS:
        binder.bind_to_constructor(mapper, mapper)