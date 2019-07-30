import discord
from discord.ext import commands
from discord import Colour, Embed, Member, Object, File

import core.utils.index
import datetime


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def leaderboard(self, ctx):
        guild = ctx.guild
        author = ctx.message.author

        ctx.db.execute("SELECT author_id, name AS author, SUM(messages_sent) AS `count` FROM leaderboard AS ldb INNER JOIN members AS mem ON mem.id = ldb.author_id WHERE guild_id = %s GROUP BY author_id ORDER BY `count` DESC LIMIT 10", (guild.id,))
        rows = ctx.db.fetchall()

        author_index = core.utils.index(rows, author=author.name)

        template = "`{index:0>2}.` {medal} `{count}` {author}"

        embed = Embed(color=0x53acf2)
        embed.add_field(name=f"FI MUNI Leaderboard! ({len(rows)})", inline=False, value="\n".join([
            template.format(index=i + 1, medal=self.get_medal(i), count=row["count"], author=row["author"])
            for i, row in enumerate(rows)
        ]))
        embed.add_field(name="Your position", inline=True, value="\n".join([
            template.format(index=j + 1, medal=self.get_medal(j), count=rows[j]["count"], author=f'**{rows[j]["author"]}**' if j == author_index else rows[j]["author"])
            for j in range(author_index - 2, author_index + 2)
            if 0 <= j < len(rows)
        ]))
        await ctx.send(embed=embed)

    def get_medal(self, i):
        return {
            0: core.utils.get(self.bot.emojis, name="gold_medal"),
            1: core.utils.get(self.bot.emojis, name="silver_medal"),
            2: core.utils.get(self.bot.emojis, name="bronze_medal")
        }.get(i, core.utils.get(self.bot.emojis, name="BLANK"))

    @commands.Cog.listener()
    async def on_message(self, message):
        guild = message.guild
        channel = message.channel
        author = message.author

        self.bot.db.execute("""
            INSERT INTO leaderboard (guild_id, channel_id, author_id, messages_sent, `timestamp`) VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE messages_sent=messages_sent+1, `timestamp`=%s
        """, (guild.id, channel.id, author.id, 1, message.created_at, message.created_at))
        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        async def catchUpAfter(timestamp):
            async for message in channel.history(limit=10000, after=timestamp, oldest_first=True):
                author = message.author

                self.bot.db.execute("""
                    INSERT INTO leaderboard (guild_id, channel_id, author_id, messages_sent, `timestamp`) VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE messages_sent=messages_sent+1, `timestamp`=%s
                """, (guild.id, channel.id, author.id, 1, message.created_at, message.created_at))
                self.bot.db.commit()

        self.bot.db.execute("""
            SELECT guild_id, channel_id, MAX(`timestamp`) AS `timestamp` FROM
                (SELECT ch.guild_id, ch.id AS `channel_id`, ldb.author_id, ldb.messages_sent, ldb.timestamp FROM channels AS ch
                LEFT OUTER JOIN leaderboard AS ldb
                ON ldb.guild_id = ch.guild_id AND ldb.channel_id = ch.id) AS restul1
            GROUP BY guild_id, channel_id
        """)
        rows = self.bot.db.fetchall()

        for row in rows:
            guild = self.bot.get_guild(row["guild_id"])
            channel = guild.get_channel(row["channel_id"])

            if not isinstance(channel, discord.TextChannel):
                continue

            timestamp_after = row["timestamp"]
            if timestamp_after:
                timestamp_after += datetime.timedelta(milliseconds=500)

            await catchUpAfter(timestamp_after)

        print("[leaderboard] is now up to date")


def setup(bot):
    bot.add_cog(Leaderboard(bot))
    print("Cog loaded: Leaderboard")
