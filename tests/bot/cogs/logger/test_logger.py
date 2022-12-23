import unittest
import unittest.mock
from datetime import datetime

import discord
import inject
from discord.ext import commands

import bot.db
import tests.helpers as helpers
from bot.cogs import logger
from bot.cogs.logger.processors import inject_backups
from tests.bot.utils import mock_database



class LoggerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.bot = helpers.MockBot(guilds=[guild])
        self.cog = logger.LoggerCog(self.bot)
        self.logger_repository = unittest.mock.AsyncMock()
        self.message_emoji_repository = unittest.mock.AsyncMock()

    @unittest.mock.patch('bot.cogs.logger.MessageIterator.history')
    async def test_backup(self, message_iterator_history) -> None:
        message_iterator_history.return_value = helpers.AsyncIterator([message1, message2])
        self.logger_repository.find_updatable_processes = unittest.mock.AsyncMock(return_value=[])
        self._mock_injections()

        await self.cog._backup()

        self.assertEqual(1, inject.instance(bot.db.GuildRepository).insert.call_count)
        self.assertEqual(2, inject.instance(bot.db.UserRepository).insert.call_count)
        self.assertEqual(1, inject.instance(bot.db.RoleRepository).insert.call_count)
        self.assertEqual(1, inject.instance(bot.db.EmojiRepository).insert.call_count)
        self.assertEqual(1, inject.instance(bot.db.CategoryRepository).insert.call_count)
        self.assertEqual(2, inject.instance(bot.db.ChannelRepository).insert.call_count)
        self.assertEqual(2, inject.instance(bot.db.MessageRepository).insert.call_count)
        self.assertEqual(3, inject.instance(bot.db.MessageEmojiRepository).insert.call_count)
        self.assertEqual(1, inject.instance(bot.db.ReactionRepository).insert.call_count)
        self.assertEqual(1, inject.instance(bot.db.AttachmentRepository).insert.call_count)

    def _mock_injections(self):
        def setup_injections(binder: inject.Binder) -> None:
            binder.install(mock_database)
            binder.install(inject_backups)
            binder.bind(commands.Bot, self.bot)
            binder.bind(bot.db.LoggerRepository, self.logger_repository)

        return inject.clear_and_configure(setup_injections)


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
    color=discord.Color.yellow(),
    created_at=datetime(2010, 11, 10, 15, 33, 00),
    guild=guild
)
guild.roles = [role1]

# emojis
emoji1 = helpers.MockEmoji(
    id=4123,
    name='kek',
    animated=False,
    created_at=datetime(2010, 11, 10, 15, 33, 00),
    guild=guild
)
guild.emojis = [emoji1]

# channels
uncategorized_channel = helpers.MockTextChannel(
    id=5123,
    name='uncategories',
    created_at=datetime(2010, 11, 10, 15, 33, 00),
    category=None,
    guild=guild
)
category = helpers.MockCategoryChannel(
    id=4123,
    name='mycategory',
    created_at=datetime(2010, 11, 10, 15, 33, 00),
    guild=guild
)
categorised_channel = helpers.MockTextChannel(
    id=5456,
    name='categorised',
    created_at=datetime(2010, 11, 10, 15, 33, 00),
    category=category,
    guild=guild
)
category.text_channels = [categorised_channel]
guild.text_channels = [uncategorized_channel, categorised_channel]
guild.categories = [category]

# messages
message1 = helpers.MockMessage(
    id=6123,
    content="Hello, I 🔖 you",
    created_at=datetime(2010, 11, 10, 15, 33, 00),
    author=member1,
    channel=categorised_channel,
    guild=guild
)
message2 = helpers.MockMessage(
    id=6456,
    content="Oh, Hi <:kek:1054601880090705940> <:kek:1054601880090705940> <a:danceblob:1054602472657780816>",
    created_at=datetime(2010, 11, 10, 15, 33, 00),
    author=member2,
    channel=categorised_channel,
    guild=guild
)
categorised_channel.history = unittest.mock.MagicMock(return_value=helpers.AsyncIterator([message1, message2]))

# reactions
reaction1 = helpers.MockReaction(
    emoji=emoji1,
    message=message1,
    count=4
)
message1.reactions = [reaction1]

# attachments
attachment1 = helpers.MockAttachment(
    content_type='plain/text',
    filename='night_sky.txt',
    url='http://google.com'
)
message1.attachments = [attachment1]
