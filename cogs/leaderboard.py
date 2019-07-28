import discord
from discord.ext import commands
from discord import Colour, Embed, Member, Object, File

import core.utils.index


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def leaderboard(self, ctx):
        guild = ctx.guild
        author = ctx.message.author

        ctx.db.execute("SELECT author_id, author, SUM(messages_sent) AS `count` FROM leaderbaord WHERE guild_id = %s GROUP BY author_id, author ORDER BY `count` DESC", (guild.id,))
        rows = ctx.db.fetchall()

        author_index = core.utils.index(rows, author=author.name)
        print(author_index)
        template = "`{index:0>2}.` {medal} `{count}` {author}"

        embed = Embed(color=0x53acf2)
        embed.add_field(name=f"FI MUNI Leaderboard! ({len(rows)})", inline=False, value="\n".join([
            template.format(index=i + 1, medal=":military_medal:", count=row["count"], author=row["author"])
            for i, row in enumerate(rows)
        ]))
        embed.add_field(name="Your position", inline=True, value="\n".join([
            template.format(index=j + 1, medal=":military_medal:", count=rows[j]["count"], author=f'**{rows[j]["author"]}**' if j == author_index else rows[j]["author"])
            for j in range(author_index - 2, author_index + 2)
            if 0 <= j < len(rows)
        ]))
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        guild = message.guild
        channel = message.channel
        author = message.author

        self.bot.db.execute("""
            INSERT INTO leaderbaord (guild_id, guild, channel_id, channel, author_id, author, messages_sent) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE messages_sent=messages_sent+1
        """, (guild.id, guild.name, channel.id, channel.name, author.id, author.name, 0))


def setup(bot):
    bot.add_cog(Leaderboard(bot))
    print("Cog loaded: Leaderboard")
