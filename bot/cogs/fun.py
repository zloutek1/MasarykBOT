import os
from io import BytesIO
from random import choice, shuffle
from urllib.parse import urlparse

import requests
import unicodeit
from disnake import Embed, File, Member, PartialEmoji
from disnake.ext import commands
from PIL import Image


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def emoji_list(self, ctx):
        await ctx.message.delete()

        emojis = sorted(ctx.guild.emojis, key=lambda emoji: emoji.name)
        for i in range(0, len(emojis), 10):
            await ctx.send(" ".join(list(map(str, emojis[i:i + 10]))))

        if len(emojis) == 0:
            await ctx.send("This guild has no emojis")

    @commands.command()
    async def emoji_url(self, ctx, emoji: PartialEmoji):
        await ctx.send(f"`{emoji.url}`")

    @commands.command(aliases=['emote'])
    async def emoji(self, ctx, emoji: PartialEmoji):
        filename = '{name}.{ext}'.format(name = emoji.name,
                                         ext="png" if not emoji.animated else "gif")

        with open(filename, 'wb') as file:
            file.write(requests.get(emoji.url).content)
        await ctx.send(file=File(filename))

        os.remove(filename)

    @commands.command(aliases=['icon_url'])
    async def logo_url(self, ctx):
        await ctx.send(f"`{ctx.guild.icon_url}`")

    @commands.command(aliases=['icon'])
    async def logo(self, ctx):
        if ctx.guild.icon is None:
            await ctx.send("this guild has no logo")
            return

        await self.send_asset(ctx, ctx.guild.icon_url)

    @commands.command()
    async def banner_url(self, ctx):
        await ctx.send(f"`{ctx.guild.banner_url}`")

    @commands.command()
    async def banner(self, ctx):
        if ctx.guild.banner is None:
            await ctx.send("this guild has no banner")
            return

        await self.send_asset(ctx, ctx.guild.banner_url)

    @commands.command()
    async def avatar_url(self, ctx):
        await ctx.send(f"`{ctx.author.avatar_url}`")

    @commands.command()
    async def avatar(self, ctx, member: Member = None):
        if member is None:
            member = ctx.author

        if member is None:
            await ctx.send(f"{member} has no avatar")
            return

        await self.send_asset(ctx, member.avatar_url)

    @commands.command(aliases=['choice', 'pick'])
    async def choose(self, ctx, *choices):
        """Chooses between multiple choices."""
        embed = Embed()

        if not choices:
            await ctx.send("no options to choose from")
            return

        extended_choices = list(choices) * 7
        for _ in range(7):
            shuffle(extended_choices)
        chosen = choice(extended_choices)

        await ctx.send_embed(" / ".join(choices), name="I choose " + chosen)

    @commands.command()
    async def hug(self, ctx, user: Member, intensity: int = 1):
        """Because everyone likes hugs"""

        emojis = ["(っ˘̩╭╮˘̩)っ", "(っ´▽｀)っ", "╰(*´︶`*)╯",
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
                  "～～(つˆДˆ)つﾉ>｡☆)ﾉ"]

        if 0 <= intensity < len(emojis):
            await ctx.send(emojis[intensity] + f" **{user}**")
        else:
            await ctx.send(choice(emojis) + f" **{user}**")

    @commands.command()
    async def answer(self, ctx, *, question):
        await ctx.send_embed(question, name=choice(("Yes", "No")))

    @commands.command()
    @commands.cooldown(rate=1, per=600, type=commands.BucketType.guild)
    async def nightsky(self, ctx):
        await ctx.send("\n".join(['.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u2002\u2002 \u3000', '\u3000\u3000\u3000˚\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*\u3000\u3000\u3000\u3000\u3000\u3000\u2008', '\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000 \u3000 \u200d \u200d \u200d \u200d \u3000\u3000\u3000\u3000 \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000,\u3000\u3000\u2002\u2002\u2002\u3000', '', '.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000ﾟ\u3000\u2002\u2002\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '', '\u3000\u3000\u3000\u3000\u3000\u3000,\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u2008\u2008\u2008\u2008\u3000\u3000\u3000\u3000:alien: doot doot', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u2008\u2008', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000:sunny:\u3000\u3000\u2008\u2008\u200a\u200a\u3000\u2008\u2008\u2008\u2008\u2008\u200a\u3000\u3000\u3000\u3000\u3000\u2008\u2008\u200a\u200a\u2008\u2008\u200a\u200a\u3000\u3000\u3000\u3000*\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u2008\u2008\u200a\u200a\u3000\u2008\u2008\u2008\u3000\u3000\u3000\u3000', '\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u2008\u2008\u200a\u200a\u3000\u2008\u2008\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u2008\u2008\u200a\u200a\u3000\u2008\u2008\u2008 ✦', '\u3000\u2002\u2002\u2002\u3000\u3000\u3000,\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*\u3000\u3000\u2008\u200a\u200a\u200a \u3000\u3000\u3000\u3000 \u3000\u3000,\u3000\u3000\u3000 \u200d \u200d \u200d \u200d \u3000 \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u3000', '\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u200a\u200a\u2008\u2008\u2008\u2008\u2008\u2008\u2008\u200a\u200a\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000˚\u3000\u3000\u3000', '\u3000 \u2002\u2002\u3000\u3000\u3000\u3000,\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u200a\u200a\u200a\u200a\u3000\u200a\u2008\u2008\u2008:rocket:\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000', '\u2008\u3000\u3000\u2002\u2002\u2002\u2002\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*', '\u3000\u3000 \u2002\u2002\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u200a\u200a\u200a\u200a\u200a\u200a\u3000\u2008\u2008\u2008\u2008\u2008\u2008\u2008\u2008\u3000\u3000\u3000\u3000', '\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u2002\u2002\u2002\u2002\u3000\u3000.', '\u3000\u2008\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000 \u3000\u3000\u3000\u3000\u3000\u200a\u200a\u200a\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u2002\u2002 \u3000', '', '\u3000˚\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000ﾟ\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u2008\u3000', '\u200d \u200d \u200d \u200d \u200d \u200d \u200d \u200d \u200d \u200d ,\u3000 \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*', '.\u3000\u3000\u3000\u3000\u3000\u2008\u3000\u3000\u3000\u3000:full_moon: \u3000\u3000\u3000\u3000\u3000\u3000\u3000:earth_americas: \u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u2002\u2002 \u3000', '\u3000\u3000\u3000˚\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000*\u3000\u3000\u3000\u3000\u3000\u3000\u2008', '\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000.', '\u3000\u3000\u2008\u3000\u3000\u3000\u3000\u3000\u3000\u3000 ✦ \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000 \u3000 \u200d \u200d \u200d \u200d \u3000\u3000\u3000\u3000 \u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000,', '']))

    @commands.command()
    async def cat(self, ctx, http_err_code: int):
        await self.send_asset(ctx, f"https://http.cat/{http_err_code}.jpg")

    @staticmethod
    async def send_asset(ctx, url: str):
        url = str(url)
        filename = os.path.basename(urlparse(url).path)

        with open(filename, 'wb') as file:
            file.write(requests.get(url).content)
        await ctx.send(file=File(filename))

        os.remove(filename)

    @commands.command()
    async def asciify(self, ctx, emoji: PartialEmoji, treshold: int = 127, size: int = 60, inverted: bool = False):
        if size < 0 or size > 300: return await ctx.send_error("Invalid image size")
        if treshold < 0 or treshold > 255: return await ctx.send_error("Invalid treshold")

        response = requests.get(emoji.url)
        img = Image.open(BytesIO(response.content)).convert('L')
        img = img.resize((size, size))

        asciiXDots = 2
        asciiYDots = 4

        ascii = ""
        for y in range(0, img.height, asciiYDots):
            line = ""
            for x in range(0, img.width, asciiXDots):
                c = self.chunk2braille( img.crop((x, y, x+asciiXDots, y+asciiYDots)), treshold, inverted )
                line += c
            ascii += line+"\n"

        if len(ascii) > 3800: return await ctx.send_error("output too large")

        await ctx.send(ascii)

    @staticmethod
    def chunk2braille( slice: Image, treshold = 127, inverted = False ):
        """https://en.wikipedia.org/wiki/Braille_Patterns"""
        dots = [ (1 + int(inverted) + int(slice.getpixel((x, y)) < treshold)) % 2
                 for y in range(slice.height)
                 for x in range(slice.width)]

        dots = [ dots[ 0 ], dots[ 2 ], dots[ 4 ], dots[ 1 ], dots[ 3 ], dots[ 5 ], dots[ 6 ], dots[ 7 ] ]

        return chr( 10240 + int( '0b' + ''.join(map(str, reversed(dots))), 2) )

    @commands.command()
    async def unicode(self, ctx, latex: str):
        """Convert latex into unicode: https://github.com/svenkreiss/unicodeit"""
        await ctx.send(unicodeit.replace(latex.strip('`')))

def setup(bot):
    bot.add_cog(Fun(bot))
