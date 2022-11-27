from typing import Dict, List, Optional, Tuple

import discord
import inject
from discord.ext import commands
from discord.utils import escape_markdown, get

from bot.cogs.utils.extra_types import GuildContext
from bot.db.leaderboard import LeaderboardRepository, Filters
from bot.db.utils import Record
from bot.utils import right_justify
from bot.cogs.utils.checks import requires_database


class LeaderboardEmbed(discord.Embed):
    def __init__(
            self,
            top10: List[Record],
            around: List[Record],
            medals: Dict[Optional[int], Optional[discord.Emoji]]
    ) -> None:
        super().__init__(color=0x53acf2)

        self.medals = medals

        self.add_field(
            inline=False,
            name="Top 10",
            value=self.make_table(top10)
        )
        self.add_field(
            inline=False,
            name="Your position",
            value=self.make_table(around)
        )

    def make_table(self, rows: List[Record]) -> str:
        if not rows:
            return "empty"
        align_digits = len(str(rows[0]["sent_total"]))

        return self.restrict_length(
            "\n".join(
                self.display_row(row, align_digits, False)
                for row in rows
            )
        )

    def display_row(self, row: Record, align_digits: int, bold: bool = False) -> str:
        position = int(row["row"])
        medal = self.medals.get(position) or self.medals[None]
        count = right_justify(row["sent_total"], align_digits, "\u2063 ")
        user = escape_markdown(row["author"])
        user = f'**{user}**' if bold else f'{user}'

        return f"`{position:0>2}.` {medal} `{count}` {user}"

    @staticmethod
    def restrict_length(string: str) -> str:
        while len(string) >= 1024:
            lines = string.split("\n")
            longest = max(((i, lines[i]) for i in range(len(lines))), key=lambda x: x[1])
            lines[longest[0]] = lines[longest[0]].rstrip("...")[:-1] + "..."
            string = "\n".join(lines)
        return string


class LeaderboardService:
    @inject.autoparams('leaderboard_repository')
    def __init__(self, leaderboard_repository: LeaderboardRepository) -> None:
        self.leaderboard_repository = leaderboard_repository

    async def get_data(self, user_id: int, filters: Filters) -> Tuple[List[Record], List[Record]]:
        await self.leaderboard_repository.preselect(filters)
        return (
            await self.leaderboard_repository.get_top10(),
            await self.leaderboard_repository.get_around(user_id)
        )


class Leaderboard(commands.Cog):
    def __init__(self, bot: commands.Bot, service: LeaderboardService = None) -> None:
        self.bot = bot
        self.service = service or LeaderboardService()

    @property
    def medals(self) -> Dict[Optional[int], Optional[discord.Emoji]]:
        return {
            None: get(self.bot.emojis, name="BLANK"),
            1: get(self.bot.emojis, name="gold_medal"),
            2: get(self.bot.emojis, name="silver_medal"),
            3: get(self.bot.emojis, name="bronze_medal")
        }

    # noinspection PyDefaultArgument
    @commands.hybrid_command()
    @commands.guild_only()
    async def leaderboard(
            self, ctx: GuildContext,
            include_channels: commands.Greedy[discord.TextChannel] = [],  # type: ignore[assignment]
            member: Optional[discord.Member] = None,
            exclude_channels: commands.Greedy[discord.TextChannel] = []  # type: ignore[assignment]
    ) -> None:
        async with ctx.typing():
            member = member if member else ctx.author
            include_channel_ids = [channel.id for channel in include_channels]
            exclude_channel_ids = [channel.id for channel in exclude_channels]
            bot_ids = [bot.id for bot in filter(lambda user: user.bot, ctx.guild.members)]

            filters = (ctx.guild.id, bot_ids, include_channel_ids, exclude_channel_ids)

            (top10, around) = await self.service.get_data(member.id, filters)
            embed = LeaderboardEmbed(top10, around, self.medals)
            await ctx.send(embed=embed)


@requires_database
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leaderboard(bot))
