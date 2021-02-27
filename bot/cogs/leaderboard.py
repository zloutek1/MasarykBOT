import re
from typing import Union, get_args
from datetime import datetime
from emoji import demojize, emojize

from discord import TextChannel, Member, Embed
from discord.ext import commands
from discord.utils import get, escape_markdown


class Emote(commands.Converter):
    REGEX = r"(?::\w+(?:~\d+)?:)"

    def __init__(self, name=None):
        self.name = name

    async def convert(self, ctx, argument):
        emote = re.search(self.REGEX, demojize(argument))

        if emote is None:
            raise commands.BadArgument(f"Emote {argument} not found")

        self.name = emote.group().strip(":")
        return self

    def __repr__(self):
        return f":{self.name}:"

    def __str__(self):
        return f":{self.name}:"


T = Union[TextChannel, Member]
U = Union[TextChannel, Member, Emote]


class Leaderboard(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def resolve_arguments(self, *args, types):
        result = []
        for _type in types:
            for arg in args:
                if isinstance(arg, _type):
                    result.append(arg)
                    break
            else:
                result.append(None)
        return tuple(result)

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def leaderboard(self, ctx, arg1: T = None, arg2: T = None):
        """
        Display the top 10 people with the most amount of messages
        and also your position with people around you

        **arguemnts** (in any order):
            @member - get a position of a specific member
            #channel - get messages in a specific channel
        """

        (channel, member) = self.resolve_arguments(arg1, arg2, types=get_args(T))

        async with ctx.typing():
            member = member if member else ctx.author
            channel_id = channel.id if channel else None
            bot_ids = [bot.id for bot in filter(lambda user: user.bot, ctx.guild.members)]

            await self.bot.db.leaderboard.preselect(ctx.guild.id, bot_ids, channel_id)
            top10 = await self.bot.db.leaderboard.get_top10()
            around = await self.bot.db.leaderboard.get_around(member.id)

            embed = await self.display_leaderboard(ctx, top10, around, member)
            await ctx.send(embed=embed)

    async def display_leaderboard(self, ctx, top10, around, member):
        def get_value(row):
            if row["author_id"] == member.id:
                return f'**{escape_markdown(row["author"])}**'
            else:
                return escape_markdown(row["author"])

        def restrict_length(string):
            while len(string) >= 1024:
                lines = string.split("\n")
                longest = max(enumerate(map(len, lines)), key=lambda x: x[1])
                lines[longest[0]] = lines[longest[0]].rstrip("...")[:-1] + "..."
                string = "\n".join(lines)
            return string

        embed = Embed(color=0x53acf2)
        embed.add_field(
            inline=False,
            name="FI MUNI Leaderboard!",
            value=restrict_length(
                        "\n".join(self.template_row(i + 1, row, top10, get_value)
                            for i, row in enumerate(top10))
                  ) or "empty result"
        )
        if around:
            embed.add_field(
                inline=False,
                name="Your position",
                value=restrict_length(
                        "\n".join(self.template_row(row["row_number"], row, around, get_value)
                                for i, row in enumerate(around))
                )
            )

        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(text=f"{str(ctx.author)} at {time_now}", icon_url=ctx.author.avatar_url)
        return embed

    def template_row(self, i, row, data, get_value):
        width = len(str(data[0].get("sent_total")))
        count = self.right_justify(row.get("sent_total"), width, "\u2063 ")

        template = "`{index:0>2}.` {medal} `{count}` {value}"

        return template.format(
            index=i,
            medal=self.get_medal(i),
            count=count,
            value=get_value(row)
        )

    @staticmethod
    def right_justify(text, by=0, pad=" "):
        return pad * (by - len(str(text))) + str(text)

    def get_medal(self, i):
        return {
            1: get(self.bot.emojis, name="gold_medal"),
            2: get(self.bot.emojis, name="silver_medal"),
            3: get(self.bot.emojis, name="bronze_medal")
        }.get(i, get(self.bot.emojis, name="BLANK"))

    @commands.command()
    @commands.cooldown(1, 900, commands.BucketType.user)
    async def emojiboard(self, ctx, arg1: U = None, arg2: U = None, arg3: U = None):
        """
        Display the top 10 most sent emojis and reactions

        **arguemnts** (in any order):
            @member - get emojis/react sent by a specific member
            #channel - get emojis/reacts in a specific channel
            :emote: - get stats of a specific emoji
        """
        (channel, member, emoji) = self.resolve_arguments(arg1, arg2, arg3, types=get_args(U))

        async with ctx.typing():
            member_id = member.id if member else None
            channel_id = channel.id if channel else None
            bot_ids = [bot.id for bot in filter(lambda user: user.bot, ctx.guild.members)]
            emoji = str(emoji) if emoji else None

            data = await self.bot.db.emojiboard.select(ctx.guild.id, bot_ids, channel_id, member_id, emoji)

            await self.display_emojiboard(ctx, data)

    async def display_emojiboard(self, ctx, data):
        def get_value(row):
            emojis = [emoji
                      for emoji in self.bot.emojis
                      if emoji.name.lower() == row["name"].strip(":").lower()
                     ]

            discord_emoji = emojis[0] if emojis else None
            demojized_emoji = emojize(row["name"])

            return discord_emoji or demojized_emoji or row["name"]

        embed = Embed(color=0x53acf2)

        value = "\n".join(self.template_row(i + 1, row, data, get_value)
                          for i, row in enumerate(data))

        embed.add_field(
            inline=False,
            name="FI MUNI Emojiboard!",
            value=value or "Empty result")

        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(text=f"{str(ctx.author)} at {time_now}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Leaderboard(bot))
