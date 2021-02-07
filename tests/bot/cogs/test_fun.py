import unittest
from unittest.mock import call

from bot.cogs import fun
from tests.mocks.discord import MockBot, MockContext, MockGuild, MockMessage, MockEmoji

class FunTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = MockBot()
        self.cog = fun.Fun(bot=self.bot)

    async def test_emoji_list_empty(self):
        emojis = []
        ctx = MockContext(bot=self.bot, guild=MockGuild(emojis=emojis))

        command = self.cog.emoji_list.callback
        await command(self.cog, ctx)

        ctx.send.assert_called_once_with("This guild has no emojis")

    async def test_emoji_list_ten_or_less(self):
        emojis = [
            MockEmoji(name="kek"),
            MockEmoji(name="cringeHarold"),
            MockEmoji(name="star")
        ]
        ctx = MockContext(bot=self.bot, guild=MockGuild(emojis=emojis))

        command = self.cog.emoji_list.callback
        await command(self.cog, ctx)

        emojis = sorted(emojis, key=lambda e: e.name)
        ctx.send.assert_called_once_with(" ".join(map(str, emojis)))

    async def test_emoji_list_more_than_ten(self):
        emojis = [
            MockEmoji(name="kek"),
            MockEmoji(name="cringeHarold"),
            MockEmoji(name="star"),
            MockEmoji(name="offline_tag"),
            MockEmoji(name="online_tag"),
            MockEmoji(name="dnd_tag"),
            MockEmoji(name="bot_tag"),
            MockEmoji(name="idle_tag"),
            MockEmoji(name="channel"),
            MockEmoji(name="pot"),
            MockEmoji(name="sleepy"),
        ]
        ctx = MockContext(bot=self.bot, guild=MockGuild(emojis=emojis))

        command = self.cog.emoji_list.callback
        await command(self.cog, ctx)

        emojis = sorted(emojis, key=lambda e: e.name)
        self.assertEqual(ctx.send.call_count, len(emojis) % 10 + 1)
        ctx.send.assert_has_calls([
            call(" ".join(str(emote) for emote in emojis[:10])),
            call(" ".join(str(emote) for emote in emojis[10:]))
        ])