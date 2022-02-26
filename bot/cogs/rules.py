from textwrap import dedent
from typing import Dict, Union

from bot.cogs.utils.context import Context, GuildChannel
from disnake import Color, Embed, Emoji, Member, TextChannel
from disnake.ext import commands
from disnake.utils import get


class Rules(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.group(name="rules", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def rules(self, ctx: Context) -> None:
        await ctx.send_help("rules")

    @rules.command(name="setup")
    async def setup_rules(self,
        ctx: Context,
        channel_name: str = "pravidla"
    ) -> None:
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
            for i in list(embeds.keys())[:-1]:
                await rules_channel.send(embed=embeds[i])

            msg_to_react_to = await rules_channel.send(embed=embeds[list(embeds.keys())[-1]])

            verify_emoji = get(self.bot.emojis, name="Verification")
            if verify_emoji is None:
                return

            await msg_to_react_to.add_reaction(verify_emoji)

        await ctx.message.delete()

    async def _get_channel(self, ctx: Context, name: str) -> TextChannel:
        assert ctx.guild, "ERROR: command can only run in guild"

        rules_channel = get(ctx.guild.text_channels, name=name)
        if rules_channel is None:
            rules_channel = await ctx.guild.create_text_channel(name)
        return rules_channel

    async def _set_permissions(self, ctx: Context, channel: TextChannel) -> None:
        assert ctx.guild, "ERROR: command can only run in guild"

        await channel.set_permissions(ctx.guild.me,
                                      add_reactions=True, send_messages=True, read_messages=True)
        await channel.set_permissions(ctx.guild.default_role,
                                      add_reactions=False, send_messages=False, read_messages=True)

    async def _get_rules(self, ctx: Context) -> Dict[int, Embed]:
        def role(name: str) -> str:
            obj = ctx.get_role(name)
            return "@" + name if obj is None else obj.mention

        def channel(name: str) -> str:
            obj = ctx.get_channel(name)
            return "#" + name if obj is None else obj.mention

        embeds: Dict[int, Embed] = {}

        embeds[0] = Embed(color=Color.blurple())
        embeds[0].set_image(
            url="https://www.fi.muni.cz/files/news-img/2168-9l6ttGALboD3Vj-jcgWlcA.jpg"
        )

        embeds[1] = Embed(
            title="{fi_muni} Vítejte na discordu Fakulty Informatiky Masarykovy Univerzity v Brně".format(
                fi_muni=ctx.get_emoji("fi_logo")
            ),
            description="⁣",
            color=Color.blurple())

        embeds[1].add_field(
            inline=False,
            name="**__Na úvod__**",
            value="• Před vstupem na náš server se prosím seznamte s pravidly, která budete muset dodržovat při interakci s ostatními uživateli a boty. Prosím berte na vědomí, že tyto pravidla nepokrývají vše za co můžete být potrestáni.")

        embeds[1].add_field(
            inline=False,
            name="​\n**__Pravidla__**",
            value=dedent(f"""
                **#1** - Neurážejte se, neznevažujte ostatní, nenadávejte.
                **#2** - Poznejte, kdy je něco debata a kdy to je už hádka.
                **#3** - Držte volnou komunikaci v {channel("shitposting")} roomce.
                **#4** - Nezatěžujte a neubližujte botům, i oni mají duši.
                **#5** - Používejte channely pro jejich daný účel.
                **#6** - Dodržujte [Discord's Terms of Service](https://discordapp.com/terms) a [Discord guidlines](https://discordapp.com/guidelines).
                **#7** - Nementionujte zbytečně role. Obzvlášť @everyone a @here. (To platí i pro adminy)
                **#8** - Chovejte se stejně, jak chcete, aby se ostatní chovali k vám."""))

        embeds[1].add_field(
            inline=False,
            name="​\n**Disclaimer**",
            value=dedent("""
                Tento server není nijak spřízněn s FI jako takovou, je to čistě studentská iniciativa bez oficiálního dohledu.
                To ovšem neznamená, že tu nejsou zaměstnanci FI - právě naopak. Z toho důvodu **důrazně doporučujeme veřejně nesdílet** příspěvky, které
                porušují školní řád, např. screeny vyplněných odpovědníků, zadání písemek atd. Pokud už se rozhodnete tak učinit, tak zodpovědnost
                nesete **sami**. Tento bot zálohuje aktivitu na tomto serveru pro analytické účely."""))

        embeds[1].add_field(
            inline=False,
            name="​\n**__Speciální místnosti__**",
            value=dedent(f"""
                Odemkni si tématické místnosti ve {channel("výběr-rolí")} a
                odemkni si předmětové místnosti ve {channel("výběr-předmětů")}."""))

        embeds[1].add_field(
            inline=False,
            name="​\n**__Užitečné linky__**",
            value=dedent("""
                ❯ [IS MUNI](https://is.muni.cz/auth)
                ❯ [ISKAM koleje]( https://iskam.skm.muni.cz/PrehledUbytovani)
                ❯ [SUPO účet (banka)](https://inet.muni.cz/app/supo/vypis)
                ❯ [katalog předmětů od 2018/2019](https://www.fi.muni.cz/catalogue2018/index.html.cs)
                ❯ [katalog předmětů od 2019/2020](https://www.fi.muni.cz/catalogue2019/)
                ❯ [harmonogram fakult](https://is.muni.cz/predmety/obdobi)
                ❯ [fi.muny.cz](http://fi.muny.cz/)
                ❯ [statistika studia](https://is.muni.cz/studium/statistika)
                ❯ [statistika kreditů](https://is.muni.cz/auth/ucitel/statistika_kreditu)
                ❯ [statistika bodů](https://is.muni.cz/auth/student/poznamkove_bloky_statistika)
                ❯ [záznamy přednášek](http://www.video.muni.cz)"""))

        embeds[1].add_field(
            inline=False,
            name="​\n**Ready?**",
            value="• Připraveni vstoupit?")

        return embeds

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


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Rules(bot))
