from disnake import Message, File, User
from disnake.ext import commands

import os
from sympy import preview
from PIL import Image, ImageDraw, ImageFont

from bot.cogs.utils import context

class LaTeX(commands.Cog):
    PADDING = 5
    ICON_SIZE = 40
    FONT_SIZE = 16

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        ctx = await self.bot.get_context(message, cls=context.Context)
        if ctx.command is not None:
            return

        count = message.content.count('$')
        if count % 2 != 0 or count == 0 or len(message.content.replace('$', '').strip()) == 0:
            return

        path = self.render(message.content, message.author.id) 
        wrapped_path = await self.wrap_with_discord_profile(path, message.author)       
        await message.channel.send(file=File(wrapped_path, filename="latex.png"))
        os.remove(wrapped_path)
        os.remove(path)


    @commands.command()
    async def latex(self, ctx, *, equation: str) -> None:
        path = self.render(f"${equation}$", ctx.author.id)
        await ctx.send(file=File(path, filename="latex.png"))
        os.remove(path)

    @staticmethod
    def render(text: str, id: int) -> str:
        filename = f'/tmp/{id}_latex.png'
        preview(
            text, 
            viewer='file', 
            filename=filename, 
            euler=False,
            dvioptions=["-bg", "Transparent", "-fg", "rgb 1.0 1.0 1.0"]
        )
        return filename

    async def wrap_with_discord_profile(self, text_path: str, user: User) -> None:
        img = Image.open(text_path)

        # extend image
        NAME_HEIGHT = self.FONT_SIZE + self.PADDING
        WIDTH = max(self.PADDING + img.width + self.ICON_SIZE + 2 * self.PADDING + self.PADDING, self.ICON_SIZE + 2 * self.PADDING + len(user.display_name) * self.FONT_SIZE)
        HEIGHT = max(self.PADDING + img.height + NAME_HEIGHT + 2 * self.PADDING, self.ICON_SIZE + 2 * self.PADDING)
        result = Image.new('RGBA', (WIDTH, HEIGHT), color = '#2C2F33')
        result.paste(img, (self.ICON_SIZE + 2 * self.PADDING, self.FONT_SIZE + 2 * self.PADDING), img)

        # paste user profile pic
        avatar = user.avatar or user.default_avatar
        await avatar.with_format("png").save(f"{user.id}_avatar.png")
        user_image = Image.open(f"{user.id}_avatar.png")
        user_image.thumbnail((self.ICON_SIZE, self.ICON_SIZE))
        mask = Image.new("L", user_image.size, 0)
        d = ImageDraw.Draw(mask)
        d.ellipse((0, 0, user_image.width, user_image.height), fill=255)
        result.paste(user_image, (self.PADDING, self.PADDING), mask)
        os.remove(f"{user.id}_avatar.png")
        
        fnt = ImageFont.truetype("bot/assets/fonts/arial.ttf", self.FONT_SIZE)
        d = ImageDraw.Draw(result)
        d.text((self.ICON_SIZE + 2 * self.PADDING, self.PADDING), user.display_name, font=fnt, fill=(255, 255, 255, 255))

        result.save(f'{user.id}_dc_message.png')
        return f'{user.id}_dc_message.png'


def setup(bot: commands.Bot) -> None:
    bot.add_cog(LaTeX(bot))
