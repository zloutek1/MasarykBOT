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

        def template_row(i, row, data):
            width = len(str(data[0].get("sent_total")))
            count = right_justify(row.get("sent_total"), width, "\u2063 ")

            template = "`{index:0>2}.` {medal} `{count}` {author}"

            return template.format(
                index=i + 1,
                medal=self.get_medal(i + 1),
                count=count,
                author=get_author(row)
            )

        author_id = member.id if member else ctx.author.id
        channel_id = channel.id if channel else None
        bots = filter(lambda user: user.bot, ctx.guild.members)
        bots_ids = [bot.id for bot in bots]

        query = """
            CREATE TEMPORARY TABLE ldb_lookup AS
                SELECT
                    ROW_NUMBER() OVER (ORDER BY sent_total DESC), *
                FROM (
                    SELECT
                        author_id,
                        author.names[1] AS author,
                        SUM(messages_sent) AS sent_total
                    FROM cogs.leaderboard
                    INNER JOIN server.users AS author
                        ON author_id = author.id
                    INNER JOIN server.channels AS channel
                        ON channel_id = channel.id
                    WHERE guild_id = $1::bigint AND
                          author_id<>ALL($2::bigint[]) AND
                          ($3::bigint IS NULL OR channel_id = $3)
                    GROUP BY author_id, author.names
                    ORDER BY sent_total DESC
                ) AS lookup
        """

        around_query = """
            WITH desired_count AS (
                SELECT sent_total
                FROM ldb_lookup
                WHERE author_id = $1)

                (
                    SELECT *
                    FROM ldb_lookup
                    WHERE sent_total >= (SELECT * FROM desired_count) AND author_id <> $1
                    ORDER BY sent_total LIMIT 2
                ) UNION (
                    SELECT *
                    FROM ldb_lookup
                    WHERE sent_total = (SELECT * FROM desired_count)
                ) UNION (
                    SELECT *
                    FROM ldb_lookup
                    WHERE sent_total < (SELECT * FROM desired_count) AND author_id <> $1 LIMIT 2
                ) ORDER BY sent_total DESC
        """

        async with ctx.acquire() as conn:
            await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY cogs.leaderboard")
            await conn.execute("DROP TABLE IF EXISTS ldb_lookup")
            await conn.execute(query, ctx.guild.id, bots_ids, channel_id)
            top10 = await conn.fetch("SELECT * FROM ldb_lookup LIMIT 10")
            aroundYou = await conn.fetch(around_query, author_id)

        embed = Embed(color=0x53acf2)
        if not member:
            embed.add_field(
                inline=False,
                name="FI MUNI Leaderboard!",
                value="\n".join(template_row(i, row, top10) for i, row in enumerate(top10)))

        embed.add_field(
            inline=False,
            name="Your position",
            value="\n".join(template_row(i, row, aroundYou) for i, row in enumerate(aroundYou)))

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
