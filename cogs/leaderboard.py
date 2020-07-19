from discord import TextChannel, Member, Embed
from discord.ext import commands
from discord.utils import get, escape_markdown

from typing import Union
from datetime import datetime


class Leaderboard(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def leaderboard(self,
                          ctx,
                          channel_or_member: Union[TextChannel, Member] = None,
                          member_or_channel: Union[Member, TextChannel] = None):
        """
        get message leaderboard from the database
        the output format is
            FI MUNI Leaderboard!
            {n}.   {count} {name}
            ... top10 ...
            Your position
            {n}.   {count} {name}
            ... +-2 around you
        optional arguments
        #channel - get messages only in one channel
        @member - get only the Your position section
        """

        channel = (channel_or_member if isinstance(channel_or_member, TextChannel) else
                   member_or_channel if isinstance(member_or_channel, TextChannel) else
                   None)

        member = (channel_or_member if isinstance(channel_or_member, Member) else
                  member_or_channel if isinstance(member_or_channel, Member) else
                  None)

        def right_justify(text, by=0, pad=" "):
            return pad * (by - len(str(text))) + str(text)

        def get_author(row):
            _id = ctx.author.id if not member else member.id
            if row["author_id"] == _id:
                return f'**{escape_markdown(row["author"])}**'
            else:
                return escape_markdown(row["author"])

        bots = filter(lambda user: user.bot, ctx.guild.members)
        bots_ids = [bot.id for bot in bots]

        top10_SQL = """
            SELECT
                author_id,
                author.names[1] AS author,
                SUM(messages_sent) AS sent_total
            FROM cogs.leaderboard
            INNER JOIN server.users AS author
                ON author_id = author.id
            INNER JOIN server.channels AS channel
                ON channel_id = channel.id
            WHERE ($1::bigint IS NULL OR channel_id = $1) AND
                  guild_id = $2::bigint AND
                  author_id<>ALL($3::bigint[])
            GROUP BY author_id, author.names
            ORDER BY sent_total DESC
            LIMIT 10
        """

        async with ctx.acquire() as conn:
            top10 = await conn.fetch(top10_SQL, channel.id if channel else None, ctx.guild.id, bots_ids)

        template = "`{index:0>2}.` {medal} `{count}` {author}"

        embed = Embed(color=0x53acf2)
        if not member:
            embed.add_field(
                inline=False,
                name="FI MUNI Leaderboard!",
                value="\n".join([
                    template.format(
                        index=i + 1,
                        medal=self.get_medal(i + 1),
                        count=right_justify(row.get("sent_total"), len(str(top10[0].get("sent_total"))), "\u2063 "),
                        author=get_author(row)
                    )
                    for i, row in enumerate(top10)
                ]))

        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(text=f"{str(ctx.author)} at {time_now}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    def get_medal(self, i):
        return {
            1: get(self.bot.emojis, name="gold_medal"),
            2: get(self.bot.emojis, name="silver_medal"),
            3: get(self.bot.emojis, name="bronze_medal")
        }.get(i, get(self.bot.emojis, name="BLANK"))


def setup(bot):
    bot.add_cog(Leaderboard(bot))
