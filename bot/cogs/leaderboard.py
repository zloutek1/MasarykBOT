import re
from datetime import datetime
from typing import (Any, Callable, List, Optional, Tuple, Type, Union, cast,
                    get_args)

from bot.cogs.utils.context import Context
from bot.db.emojiboard import EmojiboardDao
from bot.db.leaderboard import LeaderboardDao
from bot.db.utils import Record
from disnake import Embed, Emoji, Member, TextChannel
from disnake.ext import commands
from disnake.ext.commands.core import AnyContext
from disnake.utils import escape_markdown, get
from emoji import demojize, emojize


class Emote(commands.Converter):
    REGEX = r":(\w+):(\d+)?"

    def __init__(self, id: Optional[int] = None, name: Optional[str] = None) -> None:
        self.id = id
        self.name = name

    async def convert(self, _ctx: AnyContext, argument: str) -> "Emote":
        emote = re.search(self.REGEX, demojize(argument))

        if emote is None:
            raise commands.BadArgument(f"Emote {argument} not found")

        self.id = (int(emote.group(2))  if emote.group(2) is None else
                   sum(map(lambda char: ord(char), argument)))
        self.name = emote.group(1)

        return self

    def __repr__(self) -> str:
        return f":{self.name}:"

    def __str__(self) -> str:
        return f":{self.name}:"


T = Union[TextChannel, Member]
U = Union[TextChannel, Member, Emote]


class Leaderboard(commands.Cog):
    leaderboardDao = LeaderboardDao()
    emojiboardDao = EmojiboardDao()

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def resolve_arguments(*args: Any, types: Tuple[Type, ...]) -> Tuple[Any, ...]:
        result: List[Any] = []
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
    async def leaderboard(
        self,
        ctx: Context,
        arg1: Optional[T] = None,
        arg2: Optional[T] = None
    ) -> None:
        """
        Display the top 10 people with the most amount of messages
        and also your position with people around you

        **arguemnts** (in any order):
            @member - get a position of a specific member
            #channel - get messages in a specific channel
        """

        assert ctx.guild is not None, "ERROR: this method can only be used inside a guild"

        (channel, member) = self.resolve_arguments(arg1, arg2, types=get_args(T))
        channel = cast(Optional[TextChannel], channel)
        member = cast(Optional[Member], member)

        await ctx.trigger_typing()

        member = member if member else ctx.author
        channel_id = channel.id if channel else None
        bot_ids = [bot.id for bot in filter(lambda user: user.bot, ctx.guild.members)]

        await self.leaderboardDao.preselect((ctx.guild.id, bot_ids, channel_id))
        top10 = await self.leaderboardDao.get_top10()
        around = await self.leaderboardDao.get_around((member.id,))

        embed = await self.display_leaderboard(ctx, top10, around, member)
        await ctx.send(embed=embed)

    async def display_leaderboard(
        self,
        ctx: Context,
        top10: List[Record],
        around: List[Record],
        member: Member
    ) -> Embed:
        def get_value(row: Record) -> str:
            if row["author_id"] == member.id:
                return f'**{escape_markdown(row["author"])}**'
            else:
                return escape_markdown(row["author"])

        def restrict_length(string: str) -> str:
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
        embed.set_footer(
            text=f"{str(ctx.author)} at {time_now}",
            icon_url=ctx.author.avatar and ctx.author.avatar.with_format("png").url
        )
        return embed

    def template_row(
        self,
        i: int,
        row: Record,
        data: List[Record],
        get_value: Callable[[Record], str]
    ) -> str:
        width = len(str(data[0]["sent_total"]))
        count = self.right_justify(row["sent_total"], width, "\u2063 ")

        template = "`{index:0>2}.` {medal} `{count}` {value}"

        return template.format(
            index=i,
            medal=self.get_medal(i),
            count=count,
            value=get_value(row)
        )

    @staticmethod
    def right_justify(text: str, by: int = 0, pad:str = " ") -> str:
        return pad * (by - len(str(text))) + str(text)

    def get_medal(self, i: int) -> Optional[Emoji]:
        return {
            1: get(self.bot.emojis, name="gold_medal"),
            2: get(self.bot.emojis, name="silver_medal"),
            3: get(self.bot.emojis, name="bronze_medal")
        }.get(i, get(self.bot.emojis, name="BLANK"))

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def emojiboard(
        self,
        ctx: Context,
        arg1: Optional[U] = None,
        arg2: Optional[U] = None,
        arg3: Optional[U] = None
    ) -> None:
        """
        Display the top 10 most sent emojis and reactions

        **arguemnts** (in any order):
            @member - get emojis/react sent by a specific member
            #channel - get emojis/reacts in a specific channel
            :emote: - get stats of a specific emoji
        """

        assert ctx.guild is not None, "ERROR: this method can only be used inside a guild"

        (channel, member, emoji) = self.resolve_arguments(arg1, arg2, arg3, types=get_args(U))
        channel = cast(Optional[TextChannel], channel)
        member = cast(Optional[Member], member)
        emoji = cast(Optional[Emote], emoji)

        await ctx.trigger_typing()

        member_id = member.id if member else None
        channel_id = channel.id if channel else None
        bot_ids = [bot.id for bot in filter(lambda user: user.bot, ctx.guild.members)]
        emoji_id = emoji.id if emoji else None

        data = await self.emojiboardDao.select((ctx.guild.id, bot_ids, channel_id, member_id, emoji_id))

        embed =await self.display_emojiboard(ctx, data)
        await ctx.send(embed=embed)

    async def display_emojiboard(self, ctx: Context, data: List[Record]) -> Embed:
        def get_value(row: Record) -> str:
            emojis = [emoji
                      for emoji in self.bot.emojis
                      if emoji.name.lower() == row["name"].lower()]

            discord_emoji = emojis[0] if emojis else None
            demojized_emoji = emojize(':' + row["name"] + ':')

            return (str(discord_emoji) if discord_emoji is not None else
                    demojized_emoji    if demojized_emoji is not None else
                    row["name"])

        embed = Embed(color=0x53acf2)

        value = "\n".join(self.template_row(i + 1, row, data, get_value)
                          for i, row in enumerate(data))

        embed.add_field(
            inline=False,
            name="FI MUNI Emojiboard!",
            value=value or "Empty result")

        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        embed.set_footer(
            text=f"{str(ctx.author)} at {time_now}",
            icon_url=ctx.author.avatar and ctx.author.avatar.with_format("png").url
        )
        return embed


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Leaderboard(bot))
