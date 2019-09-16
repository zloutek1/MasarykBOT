from discord import Color, Embed
from discord.ext import commands
from discord.ext.commands import Bot, has_permissions

import core.utils.get


class Rules(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.group(name="rules")
    @has_permissions(administrator=True)
    async def rules(self, ctx):
        pass

    @rules.command(name="setup")
    async def setup_rules(self, ctx):
        rules_channel = core.utils.get(ctx.guild.channels, name="pravidla")
        if not rules_channel:
            rules_channel = await ctx.guild.create_text_channel("pravidla")

        await rules_channel.set_permissions(self.bot.user,
                                            add_reactions=True, send_messages=True, read_messages=True)
        await rules_channel.set_permissions(ctx.guild.default_role,
                                            add_reactions=False, send_messages=False, read_messages=True)

        mentions = {
            "NSFW": ("@NSFW"
                     if ctx.get_role("NSFW") is None else
                     ctx.get_role("NSFW").mention),
            "spam": ("#spam"
                     if ctx.get_channel("spam") is None else
                     ctx.get_channel("spam").mention),
            "shitposting": ("#shitposting"
                            if ctx.get_channel("shitposting") is None else
                            ctx.get_channel("shitposting").mention),
            "pravidla": ("#pravidla"
                         if ctx.get_channel("pravidla") is None else
                         ctx.get_channel("pravidla").mention),
            "oznámení": ("#oznámení"
                         if ctx.get_channel("oznámení") is None else
                         ctx.get_channel("oznámení").mention),
            "feedback": ("#feedback"
                         if ctx.get_channel("feedback") is None else
                         ctx.get_channel("<feedback></feedback>").mention),
            "seznamka": ("#seznamka"
                         if ctx.get_channel("seznamka") is None else
                         ctx.get_channel("seznamka").mention),
            "lidi-na-pivo": ("#lidi-na-pivo"
                             if ctx.get_channel("lidi-na-pivo") is None else
                             ctx.get_channel("lidi-na-pivo").mention)
        }

        def is_me(m):
            return m.author == self.bot.user
        await rules_channel.purge(check=is_me)

        embed = Embed(color=Color.blurple())
        embed.set_image(
            url="https://www.fi.muni.cz/files/news-img/2168-9l6ttGALboD3Vj-jcgWlcA.jpg"
        )
        await rules_channel.send(embed=embed)

        embed = Embed(
            title="{fi_muni} Vítejte na discordu Fakulty Informatiky Masarykovy Univerzity v Brně".format(
                fi_muni=ctx.get_emoji("fi_logo")
            ),
            description="⁣",
            color=Color.blurple())

        embed.add_field(
            name="**__Na úvod__**",
            value="• Před vstupem na náš server se prosím seznamte s pravidly, která budete muset dodržovat při interakci s ostatními uživateli a boty. Prosím berte na vědomí, že tyto pravidla nepokrývají vše za co můžete být potrestáni.",
            inline=False)

        embed.add_field(
            name="**__Pravidla__**",
            value="""**#1** - Neurážejte se, neznevažujte ostatní, nenadávejte
**#2** - Poznejte kdy je něco debata a kdy to je už hádka
**#3** - Držte NSFW content v {NSFW} roomkach
**#4** - Držte spamming v {spam} a {shitposting} roomkach
**#5** -  Nezatěžujte a neubližujte botům, i oni mají duši
**#6** - Používejte channely na jejich daný účel
**#7**- Dodržujte [Discord's Terms of Service](https://discordapp.com/terms) a [Discord guidlines](https://discordapp.com/guidelines).
**#8** - Nementionujte zbytečne role. Obzvlášť @everyone a @here. (To platí i pro adminy)
**#9** - Chovejte se stejne jak chcete, aby se ostatní chovali k vám.""".format(
                NSFW=mentions.get("NSFW"),
                spam=mentions.get("spam"),
                shitposting=mentions.get("shitposting")
            ),
            inline=False)

        embed.add_field(
            name="**__Užitečné linky__**",
            value="""❯ [IS MUNI](https://is.muni.cz/auth)
❯ [ISKAM koleje]( https://iskam.skm.muni.cz/PrehledUbytovani)
❯ [SUPO účet (banka)](https://inet.muni.cz/app/supo/vypis)
❯ [katalog předmětů od 2018/2019](https://www.fi.muni.cz/catalogue2018/index.html.cs)
❯ [katalog předmětů od 2019/2020](https://www.fi.muni.cz/catalogue2019/)
❯ [harmonogram fakult](https://is.muni.cz/predmety/obdobi)
❯ [fi.muny.cz](http://fi.muny.cz/)
❯ [kabell drill](https://kabell.sk/fi_muni_drill/)
❯ [statistika studia](https://is.muni.cz/studium/statistika)
❯ [statistika kreditů](https://is.muni.cz/auth/ucitel/statistika_kreditu)
❯ [statistika bodů](https://is.muni.cz/auth/student/poznamkove_bloky_statistika)""",
            inline=False)

        embed.add_field(
            name="**Ready?**",
            value="• Připravený vstoupit?",
            inline=False)
        msg_to_react_to = await rules_channel.send(embed=embed)

        verify_emoji = core.utils.get(self.bot.emojis, name="Verification")
        await msg_to_react_to.add_reaction(verify_emoji)


def setup(bot):
    bot.add_cog(Rules(bot))
