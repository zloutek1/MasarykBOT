import io
import os
import random
from ctypes.wintypes import WORD
from datetime import datetime
from enum import Enum

import disnake as discord
from disnake import ButtonStyle, ui
from disnake.ext import commands, tasks
from english_words import english_words_lower_alpha_set
from PIL import Image, ImageDraw, ImageFont

today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
random.seed(0b01110111011011110111001001100100011011000110010100001010 + today.day + today.month * 31)
WORDS = list(map(str.upper, english_words_lower_alpha_set))

class LetterStatus(Enum):
    UNSUBMITTED = (49, 51, 57)
    WRONG = (237, 66, 69)
    DISLOCATED = (201, 180, 88)
    CORRECT = (59, 165, 93)

class GameInstance:
    def __init__(self, ctx):
        self.ctx = ctx

        self.attempts = []
        self.current_attempt = []

        self.max_attempts = 6
        self.word_length = 5
        self.square_size = 30

        self.WORDS = [word for word in WORDS
                      if len(word) == self.word_length and
                         'Q' not in word and 'V' not in word]
        self.word = list(random.choice(self.WORDS))

        self.message = None
        self.controls = ControlsView(self)
        self.fp = io.BytesIO()

        self.created_at = datetime.now()

    async def input(self, letter):
        if len(self.current_attempt) >= self.word_length:
            return

        self.current_attempt.append((letter, LetterStatus.UNSUBMITTED))
        await self.display()

    async def submit(self):
        if len(self.current_attempt) == self.word_length:
            self.validate()
            self.attempts.append(self.current_attempt)
            self.current_attempt = []

        if self.did_win():
            await self.ctx.send(self.to_text())
            self.controls.stop()
            return

        if self.did_lose():
            await self.ctx.send(f"The word was {self.word}", ephemeral=True)
            self.controls.stop()
            return

        await self.display()

    async def backspace(self):
        if len(self.current_attempt) == 0:
            return
        self.current_attempt.pop()
        await self.display()

    def validate(self):
        input = self.current_attempt
        word = self.word[:]

        if len(input) < self.word_length:
            return

        for i in range(self.word_length):
            if input[i][0] == word[i]:
                input[i] = (input[i][0], LetterStatus.CORRECT)
                word[i] = "DELETED"

        for i in range(self.word_length):
            if input[i][1] != LetterStatus.UNSUBMITTED:
                continue

            try:
                index = word.index(input[i][0])
            except ValueError:
                index = -1

            if index >= 0:
                input[i] = (input[i][0], LetterStatus.DISLOCATED)
                word[index] = "DELETED"
            else:
                input[i] = (input[i][0], LetterStatus.WRONG)

        for (letter, status) in input:
            self.controls.validate_letter(letter, status)

    def did_win(self, input=None):
        input = input or self.current_attempt or self.attempts[-1]
        word = self.word[:]

        if len(input) < self.word_length:
            return False

        for i in range(self.word_length):
            if input[i][0] != word[i]:
                return False
        return True

    def did_lose(self):
        return len(self.attempts) >= self.max_attempts


    async def start(self):
        await self.ctx.send(embed=self.to_embed(),
                            view=self.controls,
                            ephemeral=True)
        self.message = await self.ctx.original_message()

    def to_embed(self):
        embed = discord.Embed(colour=discord.Colour.green())
        embed.clear_fields()
        embed.title = "Worlde"

        self.render()
        image = discord.File(f'{self.ctx.author.id}_wordle.jpeg', filename='wordle.jpeg')
        embed.set_image(file=image)

        embed.set_footer(
            text=f'Use "/worlde command" to play as well.')
        return embed


    def render(self):
        padding = 5
        width = (self.square_size + padding) * self.word_length + padding
        height = (self.square_size + padding) * self.max_attempts + padding

        img = Image.new('RGB', (width, height), color=(49, 51, 57))
        fnt = ImageFont.truetype("bot/cogs/utils/fonts/arial.ttf", self.square_size - 6)
        draw = ImageDraw.Draw(img)

        attempts = self.attempts + [self.current_attempt]

        x, y = padding, padding
        for i in range(self.max_attempts):
            for j in range(self.word_length):
                square = [(x, y),
                          (x + self.square_size, y + self.square_size)]

                if i > len(self.attempts):
                    draw.rectangle(square, fill=LetterStatus.UNSUBMITTED.value, outline=(204, 204, 204))

                else:
                    not_empty = i < len(self.attempts) or (i == len(self.attempts) and j < len(self.current_attempt))

                    fill = attempts[i][j][1].value if not_empty else LetterStatus.UNSUBMITTED.value
                    draw.rectangle(square, fill=fill, outline=(204, 204, 204))

                    if not_empty:
                        letter = attempts[i][j][0]
                        pos = (x + self.square_size / 4, y)
                        fill = (204, 204, 204) if attempts[i][j][1] in (LetterStatus.UNSUBMITTED, LetterStatus.CORRECT) else (51, 51, 51)
                        draw.text(pos, letter, font=fnt, fill=fill)

                x += self.square_size + padding
            x = padding
            y += self.square_size + padding

        img.save(f'{self.ctx.author.id}_wordle.jpeg', format="JPEG")

    def to_text(self):
        attempts = self.attempts + [self.current_attempt]

        assert len(LetterStatus) == 4
        status_map = {
            LetterStatus.WRONG: "⬛",
            LetterStatus.DISLOCATED: "🟨",
            LetterStatus.CORRECT: "🟩",
            LetterStatus.UNSUBMITTED: "🟫",
        }

        today = self.created_at.replace(hour=0, minute=0, second=0, microsecond=0)

        output = f"{today.day} / {today.month}\n\n"
        for i in range(self.max_attempts):
            for j in range(self.word_length):
                if i <= len(self.attempts):
                    not_empty = i < len(self.attempts) or (i == len(self.attempts) and j < len(self.current_attempt))
                    if not_empty:
                        output += status_map[attempts[i][j][1]]
            output += "\n"
        return output


    async def display(self):
        if not self.message:
            return
        await self.message.edit(embed=self.to_embed(), view=self.controls)
        if os.path.exists(f'{self.ctx.author.id}_wordle.jpeg'):
            os.remove(f'{self.ctx.author.id}_wordle.jpeg')

class LetterButton(ui.Button):
    def __init__(self, game, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game = game

    async def callback(self, ctx):
        await ctx.response.defer()
        await self.game.input(self.label)

class ControlsView(ui.View):
    LETTERS = ['A', 'B', 'C', 'D', 'E',
               'F', 'G', 'H', 'I', 'J',
               'K', 'L', 'M', 'N', 'O',
               'P', 'R', 'S', 'T', 'U',
               'W', 'Y', 'Z']

    def __init__(self, game):
        super().__init__()
        self.game = game

        self.letter_buttons = {
            letter: LetterButton(game, label=letter)
            for letter in self.LETTERS
        }

        self.display()

    def display(self):
        self.clear_items()

        for button in self.letter_buttons.values():
            self.add_item(button)

        async def backspace(ctx):
            await ctx.response.defer()
            await self.game.backspace()
        button = ui.Button(label="<<<", style=ButtonStyle.red)
        button.callback = backspace
        self.add_item(button)

        async def submit(ctx):
            await ctx.response.defer()
            await self.game.submit()
        button = ui.Button(label="Enter", style=ButtonStyle.green)
        button.callback = submit
        self.add_item(button)

    def validate_letter(self, letter, status):
        assert len(LetterStatus) == 4
        status_map = {
            LetterStatus.WRONG: ButtonStyle.red,
            LetterStatus.DISLOCATED: ButtonStyle.blurple,
            LetterStatus.CORRECT: ButtonStyle.green,
            LetterStatus.UNSUBMITTED: ButtonStyle.gray,
        }

        button = self.letter_buttons.get(letter)
        if not button:
            return
        button.style = status_map[status]



class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        self.scores = {}

        self.reset_wordle.start()

    @commands.slash_command(guild_ids=[573528762843660299], description="Play wordle on Discord")
    async def wordle(self, ctx):
        self.games[ctx.author.id] = GameInstance(ctx)
        game = self.games[ctx.author.id]

        await game.start()

    @tasks.loop(hours=24)
    async def reset_wordle(self):
        global today
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        random.seed(0b01110111011011110111001001100100011011000110010100001010 + today.day + today.month * 31)

        self.scores = {}
        for (user, game) in self.games.items():
            if game.did_win():
                if (today, user) not in self.scores:
                    self.scores[(today, user)] = 0
                self.scores[(today, user)] += 1

def setup(bot):
    bot.add_cog(Wordle(bot))
