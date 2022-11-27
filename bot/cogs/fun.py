from __future__ import annotations
import io
from random import choice, shuffle
from typing import TYPE_CHECKING, Literal, Optional, cast

import discord
import requests
import unicodeit
from discord.ext import commands
from PIL import Image

if TYPE_CHECKING:
    from .utils import Context, GuildContext

IMG_EXTENSIONS = Literal['webp', 'jpeg', 'jpg', 'png', 'gif']
HUGS = [
    "(っ˘̩╭╮˘̩)っ", "(っ´▽｀)っ", "╰(*´︶`*)╯",
    "(つ≧▽≦)つ", "(づ￣ ³￣)づ", "(づ｡◕‿‿◕｡)づ",
    "(づ￣ ³￣)づ", "(っ˘̩╭╮˘̩)っ", "⁽₍੭ ՞̑◞ළ̫̉◟՞̑₎⁾੭",
    "(੭ु｡╹▿╹｡)੭ु⁾⁾   ", "(*´σЗ`)σ", "(っ´▽｀)っ",
    "(っ´∀｀)っ", "c⌒っ╹v╹ )っ", "(σ･з･)σ",
    "(੭ु´･ω･`)੭ु⁾⁾", "(oﾟ▽ﾟ)o", "༼つ ் ▽ ் ༽つ",
    "༼つ . •́ _ʖ •̀ . ༽つ", "╏つ ͜ಠ ‸ ͜ಠ ╏つ", "༼ つ ̥◕͙_̙◕͖ ͓༽つ",
    "༼ つ ◕o◕ ༽つ", "༼ つ ͡ ͡° ͜ ʖ ͡ ͡° ༽つ", "(っಠ‿ಠ)っ",
    "༼ つ ◕_◕ ༽つ", "ʕっ•ᴥ•ʔっ", "", "༼ つ ▀̿_▀̿ ༽つ",
    "ʕ ⊃･ ◡ ･ ʔ⊃", "╏つ” ⊡ 〜 ⊡ ” ╏つ", "(⊃｡•́‿•̀｡)⊃",
    "(っ⇀⑃↼)っ", "(.づ◡﹏◡)づ.", "(.づσ▿σ)づ.",
    "(っ⇀`皿′↼)っ", "(.づ▣ ͜ʖ▣)づ.", "(つ ͡° ͜ʖ ͡°)つ",
    "(⊃ • ʖ̫ • )⊃", "（っ・∀・）っ", "(つ´∀｀)つ",
    "(っ*´∀｀*)っ", "(つ▀¯▀)つ", "(つ◉益◉)つ",
    " ^_^ )>",
    "───==≡≡ΣΣ((( つºل͜º)つ", "─=≡Σ((( つ◕ل͜◕)つ",
    "─=≡Σ((( つ ◕o◕ )つ", "～～～～(/￣ｰ(･･｡)/",
    "───==≡≡ΣΣ(づ￣ ³￣)づ", "─=≡Σʕっ•ᴥ•ʔっ",
    "───==≡≡ΣΣ(> ^_^ )>", "─=≡Σ༼ つ ▀̿_▀̿ ༽つ",
    "───==≡≡ΣΣ(っ´▽｀)っ", "───==≡≡ΣΣ(っ´∀｀)っ",
    "～～(つˆДˆ)つﾉ>｡☆)ﾉ"
]

with open('bot/assets/night_sky.txt', 'r') as file:
    NIGHT_SKY = file.read()


class FunService:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def list_emojis(guild: discord.Guild, columns: int = 10) -> str:
        emojis = sorted(guild.emojis, key=lambda emoji: emoji.name)
        return "\n".join(
            " ".join(
                str(emoji)
                for emoji in emojis[i:i + columns]
            )
            for i in range(0, len(emojis), columns)
        ) or "no emojis"

    def get_guild_icon_url(self, guild: discord.Guild, format: Optional[IMG_EXTENSIONS] = None) -> Optional[str]:
        return self._asset_url(guild.icon, format)

    def get_guild_banner_url(self, guild: discord.Guild, format: Optional[IMG_EXTENSIONS] = None) -> Optional[str]:
        return self._asset_url(guild.banner, format)

    def get_user_avatar_url(
            self,
            user: discord.User | discord.Member,
            format: Optional[IMG_EXTENSIONS] = None
    ) -> Optional[str]:
        return self._asset_url(user.avatar, format)

    @staticmethod
    def _asset_url(asset: Optional[discord.Asset], format: Optional[IMG_EXTENSIONS] = None) -> Optional[str]:
        if not asset:
            return None
        if format:
            fmt_asset: discord.Asset = asset.with_format(format)
            return fmt_asset.url
        return asset.url

    def asciify(
            self,
            emoji: discord.PartialEmoji,
            threshold: int = 127,
            size: int = 60,
            inverted: bool = False
    ) -> str:
        if size < 0 or size > 300:
            return "invalid image size"

        if threshold < 0 or threshold > 255:
            return "invalid threshold"

        response = requests.get(emoji.url)
        img = Image.open(io.BytesIO(response.content)).convert('L')
        img = img.resize((size, size))

        ascii_x_dots = 2
        ascii_y_dots = 4

        ascii = ""
        for y in range(0, img.height, ascii_y_dots):
            line = ""
            for x in range(0, img.width, ascii_x_dots):
                c = self._chunk2braille(img.crop((x, y, x + ascii_x_dots, y + ascii_y_dots)), threshold, inverted)
                line += c
            ascii += line + "\n"
        return ascii

    @staticmethod
    def _chunk2braille(slice: Image.Image, treshold: int = 127, inverted: bool = False) -> str:
        """https://en.wikipedia.org/wiki/Braille_Patterns"""
        dots = [(1 + int(inverted) + int(cast(int, slice.getpixel((x, y))) < treshold)) % 2
                for y in range(slice.height)
                for x in range(slice.width)]

        dots = [dots[0], dots[2],
                dots[4], dots[1],
                dots[3], dots[5],
                dots[6], dots[7]]

        return chr(10240 + int('0b' + ''.join(map(str, reversed(dots))), 2))


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot, service: FunService = None) -> None:
        self.bot = bot
        self.service = service or FunService(bot)

    @commands.command()
    @commands.guild_only()
    async def emoji_list(self, ctx: GuildContext) -> None:
        await ctx.safe_delete()
        emojis = self.service.list_emojis(ctx.guild)
        await ctx.send(emojis)

    @commands.command()
    async def emoji_url(self, ctx: Context, emoji: discord.PartialEmoji) -> None:
        await ctx.send(f"`{emoji.url}`")

    @commands.command(aliases=['emote'])
    async def emoji(self, ctx: Context, emoji: discord.PartialEmoji) -> None:
        fp = io.BytesIO(requests.get(emoji.url).content)
        await ctx.send(file=discord.File(fp))

    @commands.command()
    @commands.guild_only()
    async def icon_url(self, ctx: GuildContext, format: Optional[IMG_EXTENSIONS] = None) -> None:
        url = self.service.get_guild_icon_url(ctx.guild, format)
        await ctx.send(url or "no icon")

    @commands.command(aliases=['icon'])
    @commands.guild_only()
    async def logo(self, ctx: GuildContext) -> None:
        if not (url := self.service.get_guild_icon_url(ctx.guild)):
            await ctx.send("no icon")
        else:
            await ctx.send_asset(url)

    @commands.command()
    @commands.guild_only()
    async def banner_url(self, ctx: GuildContext, format: Optional[IMG_EXTENSIONS] = None) -> None:
        url = self.service.get_guild_banner_url(ctx.guild, format)
        await ctx.send(url or "no banner")

    @commands.command()
    @commands.guild_only()
    async def banner(self, ctx: GuildContext) -> None:
        if not (url := self.service.get_guild_banner_url(ctx.guild)):
            await ctx.send("no banner")
        else:
            await ctx.send_asset(url)

    @commands.command()
    async def avatar_url(self, ctx: Context, format: Optional[IMG_EXTENSIONS] = None) -> None:
        url = self.service.get_user_avatar_url(ctx.author, format)
        await ctx.send(url or ctx.author.default_avatar.url)

    @commands.command()
    async def avatar(self, ctx: Context, member: Optional[discord.User | discord.Member] = None) -> None:
        url = self.service.get_user_avatar_url(member or ctx.author)
        await ctx.send_asset(url or ctx.author.default_avatar.url)

    @commands.command(aliases=['choice', 'pick'])
    async def choose(self, ctx: Context, *choices: str) -> None:
        """Chooses between multiple choices."""
        if not choices:
            await ctx.send("no options to choose from")
            return

        extended_choices = list(choices) * 7
        for _ in range(7):
            shuffle(extended_choices)
        chosen = choice(extended_choices)

        await ctx.send_embed(" / ".join(choices), name="I choose " + chosen)

    @commands.command()
    async def hug(self, ctx: Context, user: discord.Member, intensity: int = 1) -> None:
        """Because everyone likes hugs"""
        if 0 <= intensity < len(HUGS):
            await ctx.send(HUGS[intensity] + f" **{user}**")
        else:
            await ctx.send(choice(HUGS) + f" **{user}**")

    @commands.command()
    async def answer(self, ctx: Context, *, question: str) -> None:
        await ctx.send_embed(question, name=choice(("Yes", "No")))

    @commands.command()
    @commands.cooldown(rate=1, per=600, type=commands.BucketType.guild)
    async def nightsky(self, ctx: Context) -> None:
        await ctx.send(NIGHT_SKY)

    @commands.command()
    async def cat(self, ctx: Context, http_err_code: int) -> None:
        await ctx.send_asset(f"https://http.cat/{http_err_code}.jpg")

    @commands.hybrid_command()
    async def asciify(self, ctx: Context, emoji: discord.PartialEmoji,
                      treshold: int = 127, size: int = 60, inverted: bool = False
                      ) -> None:
        asciified_emoji = self.service.asciify(emoji, treshold, size, inverted)
        await ctx.send(asciified_emoji)

    @commands.command()
    async def unicode(self, ctx: Context, latex: str) -> None:
        """Convert latex into unicode: https://github.com/svenkreiss/unicodeit"""
        await ctx.send(unicodeit.replace(latex.strip('`')))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))
