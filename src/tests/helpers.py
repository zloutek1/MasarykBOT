import unittest
from unittest.mock import MagicMock

import discord

from core.database import Database, Entity


def create_guild(name: str):
    guild = MagicMock(spec=discord.Guild)
    guild.id = "770041446911123456"
    guild.name = name
    guild.icon = create_icon("https://google.com")
    return guild


def create_role(name: str):
    role = MagicMock(spec=discord.Role)
    role.id = "770041446911123456"
    role.name = name
    role.color = discord.Color.from_str("0xFF00FF")
    return role


def create_icon(url: str):
    icon = MagicMock(spec=discord.Attachment)
    icon.url = url
    return icon


class RepositoryTest(unittest.IsolatedAsyncioTestCase):
    database: Database

    @classmethod
    def setUpClass(cls):
        cls.database = Database(url='sqlite+aiosqlite:///:memory:', echo=True)

    async def asyncSetUp(self) -> None:
        await self.database.create_database()
        self.session = await self.database.session().__aenter__()

    async def asyncTearDown(self) -> None:
        async with self.database._engine.begin() as conn:
            await conn.run_sync(Entity.metadata.drop_all)
