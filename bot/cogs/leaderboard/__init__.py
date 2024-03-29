from typing import Dict, Optional, Sequence

import discord
import inject
from discord.ext import commands
from discord.utils import get

from bot.cogs.leaderboard.leaderboard_embed import LeaderboardEmbed
from bot.utils import GuildContext, requires_database
from bot.db import LeaderboardRepository
from bot.db.cogs.leaderboard import LeaderboardFilter


class LeaderboardCog(commands.Cog):
    @inject.autoparams('leaderboard_repository')
    def __init__(self, bot: commands.Bot, leaderboard_repository: LeaderboardRepository) -> None:
        self.bot = bot
        self._repository = leaderboard_repository

    @property
    def medals(self) -> Dict[int | None, discord.Emoji]:
        def try_to_get(lst: Sequence[discord.Emoji], name: str) -> discord.Emoji:
            if not (emoji := get(lst, name=name)):
                raise AssertionError(f"Emoji with name {name} not found")
            return emoji

        return {
            None: try_to_get(self.bot.emojis, name="BLANK"),
            1: try_to_get(self.bot.emojis, name="gold_medal"),
            2: try_to_get(self.bot.emojis, name="silver_medal"),
            3: try_to_get(self.bot.emojis, name="bronze_medal")
        }

    # noinspection PyDefaultArgument
    @commands.hybrid_command()
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def leaderboard(
        self, ctx: GuildContext,
        include_channels: commands.Greedy[discord.TextChannel | discord.Thread] = [],  # type: ignore[assignment]
        member: Optional[discord.Member] = None,
        exclude_channels: commands.Greedy[discord.TextChannel | discord.Thread] = []  # type: ignore[assignment]
    ) -> None:
        async with ctx.typing():
            member = member if member else ctx.author
            include_channel_ids = [channel.id for channel in include_channels]
            exclude_channel_ids = [channel.id for channel in exclude_channels]
            bot_ids = [bot.id for bot in filter(lambda user: user.bot, ctx.guild.members)]

            filters = LeaderboardFilter(ctx.guild.id, bot_ids, include_channel_ids, exclude_channel_ids)
            (top10, around) = await self._repository.get_data(member.id, filters)

            embed = LeaderboardEmbed(top10, around, self.medals, member)
            await ctx.send(embed=embed)


@requires_database
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LeaderboardCog(bot))
