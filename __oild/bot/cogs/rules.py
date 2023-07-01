from textwrap import dedent
from typing import Union, Tuple

from discord import Color, Embed, Emoji, Member, TextChannel
from discord.ext import commands
from discord.utils import get

from src.bot import Context


class RulesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: Member) -> None:
        """
        Send a welcome message to DM of the new member
        with the information what to do when they join
        the server
        """

        def emoji(name: str) -> Union[Emoji, str]:
            obj = get(self.bot.emojis, name=name)
            return f":{name}:" if obj is None else obj

        await member.send(dedent(f"""
            **Vítej na discordu Fakulty Informatiky Masarykovy Univerzity v Brně**
            #pravidla a **KLIKNOUT NA {emoji("Verification")} REAKCI!!!**
            ❯ Pro vstup je potřeba přečíst
            ❯ Když jsem {emoji("status_offline")} offline, tak ne všechno proběhne hned.
            ❯ Pokud nedostanete hned roli @Student, tak zkuste odkliknout, chvíli počkat a znova zakliknout.
            """))

    @commands.group(name="rules", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def rules(self, ctx: Context) -> None:
        await ctx.send_help("rules")

    @rules.command(name="setup") # type: ignore[arg-type]
    async def setup_rules(self, ctx: Context, channel_name: str = "pravidla") -> None:
        rules_channel = await self._get_channel(ctx, channel_name)
        await self._set_permissions(ctx, rules_channel)

        embeds = await self._get_rules(ctx)

        i = 0
        async for message in rules_channel.history(oldest_first=True):
            for embed in message.embeds:
                if embed != embeds[i]:
                    await message.edit(embed=embeds[i])
                i += 1

        if i == 0:
            for i in embeds[:-1]:
                await rules_channel.send(embed=embeds[i])

            msg_to_react_to = await rules_channel.send(embed=embeds[-1])

            verify_emoji = get(self.bot.emojis, name="Verification")
            if verify_emoji is None:
                return

            await msg_to_react_to.add_reaction(verify_emoji)

        await ctx.message.delete()

    @staticmethod
    async def _get_channel(ctx: Context, name: str) -> TextChannel:
        assert ctx.guild, "ERROR: command can only run in guild"

        rules_channel = get(ctx.guild.text_channels, name=name)
        if rules_channel is None:
            rules_channel = await ctx.guild.create_text_channel(name)
        return rules_channel

    @staticmethod
    async def _set_permissions(ctx: Context, channel: TextChannel) -> None:
        assert ctx.guild, "ERROR: command can only run in guild"

        await channel.set_permissions(ctx.guild.me,
                                      add_reactions=True, send_messages=True, read_messages=True)
        await channel.set_permissions(ctx.guild.default_role,
                                      add_reactions=False, send_messages=False, read_messages=True)

    @staticmethod
    async def _get_rules(ctx: Context) -> Tuple[Embed, ...]:
        # noinspection PyUnusedLocal
        def role(name: str) -> str:
            obj = ctx.get_role(name)
            return "@" + name if obj is None else obj.mention

        def channel(name: str) -> str:
            obj = ctx.get_channel(name)
            return "#" + name if obj is None else obj.mention

        with open('bot/assets/rules.txt') as file:
            rules = file.read()
            sections = rules.split("\n\n")

        cover = Embed(color=Color.blurple())
        cover.set_image(
            url="https://www.fi.muni.cz/files/news-img/2168-9l6ttGALboD3Vj-jcgWlcA.jpg"
        )

        rule_embed = Embed(
            title=sections[0].format(fi_logo=ctx.get_emoji("fi_logo")),
            color=Color.blurple()
        )

        for section in sections[1:]:
            name, value = section.split('\n', 1)
            rule_embed.add_field(inline=False, name="\n\u200b\n" + name, value=value.format(
                shitposting=channel("shitposting"),
                off_topic=channel("off-topic"),
                vyber_roli=channel("výběr-rolí"),
                vvber_predmetu=channel("výběr-předmětů"),
            ))

        return cover, rule_embed


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RulesCog(bot))
