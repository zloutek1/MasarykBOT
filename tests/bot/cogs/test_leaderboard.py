import unittest
from unittest.mock import call

from bot.cogs import leaderboard
from bot.cogs.leaderboard import Emote

from discord import Member, TextChannel

from tests.mocks.discord import MockBot, MockContext, MockMember, MockTextChannel, MockEmoji
from tests.mocks.database import MockLeaderboardRecord

class LeaderboardTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.medals = [
            MockEmoji(name='gold_medal'),
            MockEmoji(name='silver_medal'),
            MockEmoji(name='bronze_medal'),
            MockEmoji(name='BLANK')
        ]

        self.bot = MockBot(emojis=self.medals)
        self.cog = leaderboard.Leaderboard(bot=self.bot)

    async def test_resolve_arguments(self):
        member = MockMember(name="Bob")
        channel = MockTextChannel(name="general")
        emote = Emote(name="kek")

        result = self.cog.resolve_arguments(member, channel, types=[Member, TextChannel])
        self.assertEqual(result, (member, channel))

        result = self.cog.resolve_arguments(channel, member, types=[Member, TextChannel])
        self.assertEqual(result, (member, channel))

        result = self.cog.resolve_arguments(member, channel, emote, types=[Member, TextChannel, Emote])
        self.assertEqual(result, (member, channel, emote))

        result = self.cog.resolve_arguments(member, emote, channel, types=[Member, TextChannel, Emote])
        self.assertEqual(result, (member, channel, emote))

        result = self.cog.resolve_arguments(emote, member, channel, types=[Member, TextChannel, Emote])
        self.assertEqual(result, (member, channel, emote))

        result = self.cog.resolve_arguments(emote, channel, member, types=[Member, TextChannel, Emote])
        self.assertEqual(result, (member, channel, emote))

    async def test_display_empty_leaderboard(self):
        ctx = MockContext()
        member = MockMember()

        embed = await self.cog.display_leaderboard(ctx, [], [], member)
        self.assertEqual(len(embed.fields), 1)
        self.assertEqual(embed.fields[0].name, 'FI MUNI Leaderboard!')
        self.assertEqual(embed.fields[0].value, 'empty result')

    async def test_display_leaderboard_of_member_with_no_messages(self):
        ctx = MockContext()
        member = MockMember()

        top10 = [
            MockLeaderboardRecord(row_number=1, author_id=1,   author='Best#1234', sent_total=150),
            MockLeaderboardRecord(row_number=2, author_id=222, author='Cool#1154', sent_total=101),
            MockLeaderboardRecord(row_number=3, author_id=36,  author='Loser#1236', sent_total=2)
        ]

        expected = (f"`01.` {self.medals[0]} `150` Best#1234\n" +
                    f"`02.` {self.medals[1]} `101` Cool#1154\n" +
                    f"`03.` {self.medals[2]} `\u2063 \u2063 2` Loser#1236")

        embed = await self.cog.display_leaderboard(ctx, top10, [], member)

        self.assertEqual(len(embed.fields), 1)
        self.assertEqual(embed.fields[0].name, 'FI MUNI Leaderboard!')
        self.assertEqual(embed.fields[0].value, expected)

    async def test_display_leaderboard_of_member_in_top_ten(self):
        ctx = MockContext()
        member = MockMember(id=222, name="Best#1234")

        top10 = [
            MockLeaderboardRecord(row_number=1, author_id=1,   author='Best#1234', sent_total=150),
            MockLeaderboardRecord(row_number=2, author_id=222, author='Cool#1154', sent_total=101),
            MockLeaderboardRecord(row_number=3, author_id=36,  author='Loser#1236', sent_total=2)
        ]

        around = top10

        expected = (f"`01.` {self.medals[0]} `150` Best#1234\n" +
                    f"`02.` {self.medals[1]} `101` **Cool#1154**\n" +
                    f"`03.` {self.medals[2]} `\u2063 \u2063 2` Loser#1236")

        embed = await self.cog.display_leaderboard(ctx, top10, around, member)

        self.assertEqual(len(embed.fields), 2)
        self.assertEqual(embed.fields[0].name, 'FI MUNI Leaderboard!')
        self.assertEqual(embed.fields[0].value, expected)
        self.assertEqual(embed.fields[1].name, 'Your position')
        self.assertEqual(embed.fields[1].value, expected)