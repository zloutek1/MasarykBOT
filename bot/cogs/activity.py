from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional

import pandas as pd
from bot.cogs.utils import heatmap
from disnake import File, Member
from disnake.ext import commands


class Activity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def activity(self, ctx, member: Optional[Member] = None, past_days: int = 365):
        """
        Show frequency of messages sent
        |past_days| <= 365
        """

        member_id = member.id if member else None

        past_days = min(abs(past_days), 365)
        past_days = 7 * round(past_days / 7)

        tomorrow = (datetime.now()
                        .replace(hour=0, minute=0, second=0, microsecond=0)
                + timedelta(days=1))
        past = tomorrow - timedelta(days=past_days + tomorrow.weekday())

        rows = await self.bot.db.activity.select(ctx.guild.id, member_id, past, tomorrow)
        series = self.prepare_data(rows, from_date=past, to_date=tomorrow)

        fig = heatmap.generate_heatmap(series)

        with BytesIO() as buffer:
            fig.savefig(buffer, format="PNG", bbox_inches="tight", dpi=400)
            buffer.seek(0)
            await ctx.reply(file=File(buffer, filename=f"{member_id}_activity.png"))


    @staticmethod
    def prepare_data(data, from_date: datetime, to_date: datetime):
        data = pd.Series(dict(data))
        data.index = pd.DatetimeIndex(data.index)

        idx = pd.date_range(from_date, to_date)
        return data.reindex(idx, fill_value=0)


def setup(bot):
    bot.add_cog(Activity(bot))
