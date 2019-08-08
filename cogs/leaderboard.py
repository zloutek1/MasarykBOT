import discord
from discord.ext import commands
from discord import Colour, Embed, Member, Object, File
from discord.channel import TextChannel

from typing import Optional, Union

import core.utils.index
import datetime

from core.utils.checks import needs_database


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.readyCogs[self.__class__.__name__] = False

        self.bot.add_catchup_task("leaderboard", self.catchup_leaderboard)

        self.bot.readyCogs[self.__class__.__name__] = True

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command()
    @needs_database
    async def leaderboard(self, ctx, channel: Optional[Union[TextChannel, Member]] = None, member: Optional[Union[Member, TextChannel]] = None):

        channel, member = (channel if isinstance(channel, TextChannel) else
                           member if isinstance(member, TextChannel) else
                           None,

                           member if isinstance(member, Member) else
                           channel if isinstance(channel, Member) else
                           None)

        guild = ctx.guild
        author = ctx.message.author

        params = {"guild_id": guild.id}

        if channel:
            params["channel_id"] = channel.id

        if member:
            params["author_id"] = member.id
        else:
            params["author_id"] = author.id

        top10_SQL = f"""
            SELECT
                author_id,
                name AS author,
                SUM(messages_sent) AS `count`
            FROM leaderboard AS ldb
            INNER JOIN `member` AS mem
            ON mem.id = ldb.author_id
            WHERE guild_id = %(guild_id)s {'AND channel_id = %(channel_id)s' if channel is not None else ''}
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
            CREATE TEMPORARY TABLE lookup SELECT `row_number`, author_id, author, `count` FROM (
                SELECT
                    (ROW_NUMBER() OVER (ORDER BY `count` DESC)) AS `row_number`,
                    author_id,
                    author,
                    `count`
                FROM (
                    SELECT
                        author_id,
                        name AS author,
                        SUM(messages_sent) AS `count`
                    FROM leaderboard AS ldb
                    INNER JOIN `member` AS mem
                    ON mem.id = ldb.author_id
                    WHERE guild_id = %(guild_id)s {'AND channel_id = %(channel_id)s' if channel is not None else ''}
                    GROUP BY author_id
                    ORDER BY `count` DESC) AS sel
                ) AS sel;
            SET @desired_count = (SELECT `count` FROM lookup WHERE author_id = @desired_id);
            CREATE TEMPORARY TABLE first_table SELECT * FROM lookup WHERE `count` >= @desired_count AND author_id <> @desired_id ORDER BY `count` LIMIT 2;
            CREATE TEMPORARY TABLE middle_table SELECT * FROM lookup WHERE author_id = @desired_id;
            CREATE TEMPORARY TABLE  last_table SELECT * FROM lookup WHERE `count` < @desired_count AND author_id <> @desired_id LIMIT 2;
            SELECT * from (SELECT * FROM first_table UNION ALL SELECT * FROM middle_table UNION ALL SELECT * FROM last_table) result ORDER BY `count` DESC;
        """

        ctx.db.execute(top10_SQL, params)
        rows1 = ctx.db.fetchall()

        result = ctx.db.execute(member_SQL, params, multi=True)
        rows2 = list(result)[10].fetchall()
        ctx.db.commit()

        """
        print the leaderboard
        """

        author_index = core.utils.index(rows1, author=author.name)

        template = "`{index:0>2}.` {medal} `\u3000{count: >{top}}` {author}"

        embed = Embed(color=0x53acf2)
        if not member:
            embed.add_field(
                name=f"FI MUNI Leaderboard! ({len(rows1)})",
                inline=False,
                value="\n".join([
                    template.format(
                        index=i + 1,
                        medal=self.get_medal(i + 1),
                        count=row["count"],
                        author=row["author"],
                        top=len(str(rows1[0]["count"]))
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
                    count=row["count"],
                    author=(f'**{row["author"]}**'
                            if row["author_id"] == (
                                author.id if not member else member.id)
                            else
                            row["author"]),
                    top=len(str(rows2[0]["count"]))
                )
                for j, row in enumerate(rows2)
            ]))
        await ctx.send(embed=embed)

    def get_medal(self, i):
        return {
            1: core.utils.get(self.bot.emojis, name="gold_medal"),
            2: core.utils.get(self.bot.emojis, name="silver_medal"),
            3: core.utils.get(self.bot.emojis, name="bronze_medal")
        }.get(i, core.utils.get(self.bot.emojis, name="BLANK"))

    async def catchup_leaderboard(self, db, message):
        db.execute("""
            INSERT INTO leaderboard (guild_id, channel_id, author_id, messages_sent, `timestamp`) VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE messages_sent=messages_sent+1, `timestamp`=%s
                    """, (message.guild.id, message.channel.id, message.author.id, 1, message.created_at, message.created_at))
        db.commit()


def setup(bot):
    bot.add_cog(Leaderboard(bot))
    print("Cog loaded: Leaderboard")
