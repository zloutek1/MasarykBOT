import unittest
from datetime import datetime

import discord

import tests.helpers as helpers
from bot.cogs import logger


class LoggerTests(unittest.IsolatedAsyncioTestCase):
    async def test_backup(self) -> None:
        await logger.GuildBackup().traverseDown(guild)



# ---- data ---- #

# guilds
guild = helpers.MockGuild(
    id=1123, 
    name='Large guild',
    icon=None,
    created_at=datetime(2022, 11, 10, 15, 33, 00),
)

# members
member1 = helpers.MockMember(
    id=2123,
    name='Will',
    avatar=None,
    bot=False,
    created_at=datetime(2010, 11, 10, 15, 33, 00),
    guild=guild
)  
member2 = helpers.MockMember(
    id=2456,
    name='BOT',
    avatar=None,
    bot=True,
    created_at=datetime(2010, 11, 10, 15, 33, 00),
    guild=guild
)
guild.members = [member1, member2]

# roles
role1 = helpers.MockRole(
    id=3123,
    name='Admin',
    color=discord.Color.yellow,
    created_at=datetime(2010, 11, 10, 15, 33, 00),
    guild=guild
)
guild.roles = [role1]


# channels
uncategories_channel = helpers.MockTextChannel(
    id=5123,
    name='uncategories',
    category=None,
    guild=guild
)
category = helpers.MockCategoryChannel(
    id=4123,
    name='mycategory',
    guild=guild
)
categorised_channel = helpers.MockTextChannel(
    id=5456,
    name='categorised',
    category=category,
    guild=guild
)
category.text_channels = [categorised_channel]
guild.text_channels = [uncategories_channel, categorised_channel]
guild.categories = [category]

# messages
message1 = helpers.MockMessage(
    id=6123,
    content="Hello",
    author=member1,
    channel=categorised_channel,
    guild=guild
)
message2 = helpers.MockMessage(
    id=6456,
    content="Oh, Hi",
    author=member2,
    channel=categorised_channel,
    guild=guild
)
categorised_channel.history = unittest.mock.MagicMock(return_value=helpers.AsyncIterator([message1, message2]))
