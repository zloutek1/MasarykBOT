from discord.ext import commands
from discord import Embed, Member
from discord.channel import TextChannel

import re
import logging
from emoji import UNICODE_EMOJI
from typing import Union

import core.utils.get
import core.utils.index

from core.utils.db import Database
from core.utils.checks import needs_database


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

    @needs_database
    async def catchup_leaderboard_get(self, message, leaderboard_data: dict, *, db: Database = None):
        """
        format message in format
            (guild_id, channel_id, author_id, count, created_at)
        append the data into leaderboard_data
        if the message is not a bot command
        """
        c = message.content.lower()
        if c.startswith("!") or c.startswith("pls"):
            return

        key = (message.guild.id, message.channel.id, message.author.id)
        entry = leaderboard_data.get(key, (0, None))
        leaderboard_data[key] = (entry[0] + 1, message.created_at)

    @needs_database
    async def catchup_leaderboard_insert(self, leaderboard_data: dict, *, db: Database = None):
        """
        insert the leaderboard_data into the
        database in chunks
        """
        leaderboard_data = [key + val for key, val in leaderboard_data.items()]
        chunks = self.chunks(leaderboard_data, 550)
        for i, chunk in enumerate(chunks):
            await db.executemany("""
                INSERT IGNORE INTO leaderboard
                    (guild_id, channel_id, author_id, messages_sent, `timestamp`)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE messages_sent = messages_sent+1
            """, chunk)

            await db.commit()
            self.log.info(
                f"Saved {(i + 1) * 550} rows for leaderboard to database")

    """--------------------------------------------------------------------------------------------------------------------------"""

    @needs_database
    async def catchup_leaderboard_emoji_get(self, message, leaderboard_emoji_data: dict, *, db: Database = None):
        """
        format each emoji in message in format
            (guild_id, channel_id, emoji, count, created_at)
        append the data into leaderboard_emoji_data
        """
        c = message.content.lower()

        emojis = (re.findall(r"\<\:\w+\:(\d+)\>", c) +
                  [em for em in c if em in UNICODE_EMOJI] +
                  re.findall(r"(?:\s|^)(:\)|<3|:\(|;\(|:P|:\*|:o|:'\))(?:\s|$)", c))

        for emoji in emojis:
            if emoji.isdigit():
                emoji = self.bot.get_emoji(int(emoji))
                if emoji is None:
                    emoji = core.utils.get(self.bot.emojis, name="nitroEmotes")

                emoji = emoji.id

            key = (message.guild.id, message.channel.id, emoji)
            entry = leaderboard_emoji_data.get(key, (0, None))
            leaderboard_emoji_data[key] = (entry[0] + 1, message.created_at)

    @needs_database
    async def catchup_leaderboard_emoji_insert(self, leaderboard_emoji_data, *, db: Database = None):
        """
        insert the leaderboard_emoji_data into the
        database in chunks
        """
        leaderboard_emoji_data = [key + val for key,
                                  val in leaderboard_emoji_data.items()]
        chunks = self.chunks(leaderboard_emoji_data, 550)
        for i, chunk in enumerate(chunks):
            await db.executemany("""
                INSERT INTO leaderboard_emoji
                    (guild_id, channel_id, emoji, sent_times, `timestamp`)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE sent_times=sent_times+1
            """, chunk)
            await db.commit()
            self.log.info(
                f"Saved {(i + 1) * 550} rows for leaderboard_emoji to database")

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.Cog.listener()
    async def on_ready(self):
        """
        check if core.logger Cog is loaded (has add_catchup_task variable)
        add catchup_methods to the bot
        """

        self.bot.readyCogs[self.__class__.__name__] = False

        if hasattr(self.bot, "add_catchup_task"):
            self.bot.add_catchup_task(
                "leaderboard", self.catchup_leaderboard_get, self.catchup_leaderboard_insert, task_data=dict())

            self.bot.add_catchup_task(
                "leaderboard_emoji", self.catchup_leaderboard_emoji_get, self.catchup_leaderboard_emoji_insert, task_data=dict())

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
                        count=right_justify(row["count"], len(
                            str(rows1[0]["count"])), "\u2063 "),
                        author=f'**{row["author"]}**'
                        if row["author_id"] == (
                            author.id if not member else member.id)
                        else
                        row["author"]
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
                    count=right_justify(row["count"], len(
                        str(rows1[0]["count"])), "\u2063 "),
                    author=(f'**{row["author"]}**'
                            if row["author_id"] == (
                                author.id if not member else member.id)
                            else
                            row["author"])
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

    """--------------------------------------------------------------------------------------------------------------------------"""

    @commands.command(name="emojiboard", aliases=("emoji_leaderboard", "leadermoji"))
    @needs_database
    async def emojiboard(self, ctx, channel: TextChannel = None, *, db: Database = None):
        """
        get message leaderboard from the database
        the output format is
            FI MUNI emoji Leaderboard!
            {n}.   {emoji} ......... {count}
            ... top10 ...

            Nitro {count}

        optional arguments
        #channel - get emojis only in one channel
        """

        channel = channel if isinstance(channel, TextChannel) else None

        guild = ctx.guild

        params = {"guild_id": guild.id}

        if channel:
            params["channel_id"] = channel.id

        top10_SQL = f"""
            SELECT
                emoji,
                SUM(sent_times) AS `count`
            FROM leaderboard_emoji AS ldb
            WHERE emoji != "617744996497621025" AND
            guild_id = %(guild_id)s {'AND channel_id = %(channel_id)s' if channel is not None else ''}
            GROUP BY emoji
            ORDER BY `count` DESC
            LIMIT 10
        """

        await db.execute(top10_SQL, params)
        rows = await db.fetchall()

        nitro_SQL = f"""
        SELECT
            emoji,
            SUM(sent_times) AS `count`
        FROM leaderboard_emoji AS ldb
        WHERE emoji = "617744996497621025" AND
        guild_id = %(guild_id)s {'AND channel_id = %(channel_id)s' if channel is not None else ''}
        GROUP BY emoji
        ORDER BY `count` DESC
        LIMIT 1;
        """
        await db.execute(nitro_SQL, params)
        nitro_row = await db.fetchone()

        """
        print the emoji leaderboard
        """
        def right_justify(text, by=0, pad=" "):
            return pad * (by - len(str(text))) + str(text)

        template = "`{index:0>2}.` {emoji} `{count:.>20}`"

        embed = Embed(color=0x53acf2)
        embed.add_field(
            name=f"FI MUNI emoji Leaderboard! ({len(rows)})",
            inline=False,
            value="\n".join([
                template.format(
                    index=i + 1,
                    count=row["count"],
                    emoji=self.bot.get_emoji(
                        int(row["emoji"])) if row["emoji"].isdigit() else row["emoji"]
                )
                for i, row in enumerate(rows)
            ]))
        embed.add_field(
            name="Nitro emojis",
            inline=False,
            value="{emoji} `{count}`".format(
                count=right_justify(nitro_row["count"], len(
                    str(nitro_row["count"])), "\u2063 "),
                emoji=self.bot.get_emoji(int(nitro_row["emoji"])),
            )
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Leaderboard(bot))
