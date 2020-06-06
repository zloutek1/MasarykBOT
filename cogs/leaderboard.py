from discord.ext import commands
from discord import Embed, Member, File
from discord.channel import TextChannel
from discord.utils import escape_markdown

import logging
from typing import Union

import matplotlib.pyplot as plt
import numpy as np
from scipy import interpolate

import core.utils.get
import core.utils.index

from core.utils.db import Database
from core.utils.checks import needs_database

from datetime import datetime


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger(__name__)

    """--------------------------------------------------------------------------------------------------------------------------"""

    @staticmethod
    def chunks(l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.readyCogs[self.__class__.__name__] = False

        #
        # leaderboard is updated via database trigger command
        #

        self.bot.readyCogs[self.__class__.__name__] = True

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    @needs_database
    async def leaderboard(self, ctx, channel: Union[TextChannel, Member] = None, member: Union[Member, TextChannel] = None, *, db: Database = None):
        channel, member = (channel if isinstance(channel, TextChannel) else
                           member if isinstance(member, TextChannel) else
                           None,

                           member if isinstance(member, Member) else
                           channel if isinstance(channel, Member) else
                           None)
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

        author = ctx.message.author

        bots = core.utils.get(ctx.guild.members, key=lambda user: user.bot)
        bots_ids = list(map(lambda bot: bot.id, bots))

        params = {
            "guild_id": ctx.guild.id,
            "channel_id": channel.id if channel else None,
            "author_id": member.id if member else author.id,
            "ignored_ids": tuple(bots_ids)
        }

        top10_SQL = f"""
            SELECT
                author_id,
                mem.name AS author,
                SUM(messages_sent) AS `count`
            FROM leaderboard AS ldb
            INNER JOIN `member` AS mem
            ON mem.id = ldb.author_id
            INNER JOIN `channel` AS chnl
            ON chnl.id = channel_id
            WHERE {'channel_id = %(channel_id)s' if channel is not None else '1'} AND guild_id = %(guild_id)s AND author_id NOT IN %(ignored_ids)s
            GROUP BY author_id
            ORDER BY `count` DESC
            LIMIT 10
        """

        member_SQL = f"""
            DROP TEMPORARY TABLE IF EXISTS lookup;
            DROP TEMPORARY TABLE IF EXISTS first_table;
            DROP TEMPORARY TABLE IF EXISTS middle_table;
            DROP TEMPORARY TABLE IF EXISTS last_table;

            SET @desired_id = %(author_id)s;
            SET @row_number = 0;
            CREATE TEMPORARY TABLE lookup SELECT `row_number`, author_id, author, `count` FROM (
                SELECT
                    (@row_number:=@row_number + 1) AS `row_number`,
                    author_id,
                    author,
                    `count`
                FROM (
                    SELECT
                        author_id,
                        mem.name AS author,
                        SUM(messages_sent) AS `count`
                    FROM leaderboard AS ldb
                    INNER JOIN `member` AS mem
                    ON mem.id = ldb.author_id
                    INNER JOIN `channel` AS chnl
                    ON chnl.id = channel_id
                    WHERE {'channel_id = %(channel_id)s' if channel is not None else '1'} AND guild_id = %(guild_id)s AND author_id NOT IN %(ignored_ids)s
                    GROUP BY author_id
                    ORDER BY `count` DESC) AS sel
                ) AS sel;
            SET @desired_count = (SELECT `count` FROM lookup WHERE author_id = @desired_id);
            CREATE TEMPORARY TABLE first_table SELECT * FROM lookup WHERE `count` >= @desired_count AND author_id <> @desired_id ORDER BY `count` LIMIT 2;
            CREATE TEMPORARY TABLE middle_table SELECT * FROM lookup WHERE author_id = @desired_id;
            CREATE TEMPORARY TABLE  last_table SELECT * FROM lookup WHERE `count` < @desired_count AND author_id <> @desired_id LIMIT 2;
        """

        await db.execute(top10_SQL, params)
        rows1 = await db.fetchall()

        await db.execute(member_SQL, params)
        await db.execute("SELECT * from (SELECT * FROM first_table UNION ALL SELECT * FROM middle_table UNION ALL SELECT * FROM last_table) result ORDER BY `count` DESC;")
        rows2 = await db.fetchall()

        """
        print the leaderboard
        """
        def right_justify(text, by=0, pad=" "):
            return pad * (by - len(str(text))) + str(text)

        def get_author(row):
            _id = author.id if not member else member.id
            if row["author_id"] == _id:
                return f'**{escape_markdown(row["author"])}**'
            else:
                return escape_markdown(row["author"])

        template = "`{index:0>2}.` {medal} `{count}` {author}"

        embed = Embed(color=0x53acf2)
        if not member:
            embed.add_field(
                name=f"FI MUNI Leaderboard! ({len(rows1)})",
                inline=False,
                value="\n".join([
                    template.format(
                        index=i + 1,
                        medal=self.get_medal(i + 1),
                        count=right_justify(row["count"], len(str(rows1[0]["count"])), "\u2063 "),
                        author=get_author(row)
                    )
                    for i, row in enumerate(rows1)
                ]))

        embed.add_field(
            name="Your position",
            inline=True,
            value="\n".join([
                template.format(
                    index=row["row_number"],
                    medal=self.get_medal(row["row_number"]),
                    count=right_justify(row["count"], len(str(rows1[0]["count"])), "\u2063 "),
                    author=get_author(row)
                )
                for j, row in enumerate(rows2)
            ]))

        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(text=f"{str(author)} at {time_now}", icon_url=author.avatar_url)
        await ctx.send(embed=embed)

    def get_medal(self, i):
        return {
            1: core.utils.get(self.bot.emojis, name="gold_medal"),
            2: core.utils.get(self.bot.emojis, name="silver_medal"),
            3: core.utils.get(self.bot.emojis, name="bronze_medal")
        }.get(i, core.utils.get(self.bot.emojis, name="BLANK"))

    @commands.command("graph")
    @commands.cooldown(1, 120, commands.BucketType.channel)
    @needs_database
    async def graph(self, ctx, *, db: Database = None):
        await db.execute("select extract( hour from created_at ) as hr, extract( minute from created_at ) as min, count( id ) from message group by hr, min order by hr, min")
        rows = await db.fetchall()

        values = list(map(lambda x: tuple(x.values()), rows))
        xs = [t[0] * 60 * 60 + t[1] * 60 for t in values]
        ys = [t[2] for t in values]

        x_new = np.linspace(0, 86340, 86340)
        a_BSpline = interpolate.make_interp_spline(xs, ys)
        y_new = a_BSpline(x_new)

        plt.plot(x_new, y_new)
        plt.ylabel('msg/day')
        plt.savefig('assets/graph.png')

        await ctx.send(file=File('assets/graph.png'))


def setup(bot):
    bot.add_cog(Leaderboard(bot))
