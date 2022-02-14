import io
import os
import random
from collections import defaultdict
from ctypes.wintypes import WORD
from datetime import datetime
from enum import Enum
from typing import List

import disnake as discord
from bot.constants import Config
from disnake import ButtonStyle, ui
from disnake.ext import commands, tasks
from english_words import english_words_lower_alpha_set
from PIL import Image, ImageDraw, ImageFont


class LetterStatus(Enum):
    UNSUBMITTED = (49, 51, 57)
    WRONG = (237, 66, 69)
    DISLOCATED = (201, 180, 88)
    CORRECT = (59, 165, 93)

class GameInstance:
    def __init__(self, ctx, words: List[str], nth: int=0):
        self.ctx = ctx
        self.nth = nth

        self.attempts = []
        self.current_attempt = []

        self.max_attempts = 6
        self.word_length = 5
        self.square_size = 30

        self.WORDS = [word for word in words
                      if len(word) == self.word_length and
                         'Q' not in word and 'V' not in word]
        self.word = list(self.WORDS[nth % len(self.WORDS)])

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
        if len(self.current_attempt) != self.word_length:
            return

        word = ''.join(letter[0] for letter in self.current_attempt)
        if word not in self.WORDS:
            await self.ctx.send(f"*{word}* is not a word", ephemeral=True)
            return

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
        input = input or self.current_attempt or (self.attempts and self.attempts[-1])
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
        embed.title = "Wordle"

        self.render()
        image = discord.File(f'/tmp/{self.ctx.author.id}_wordle.jpeg', filename='wordle.jpeg')
        embed.set_image(file=image)

        embed.set_footer(
            text=f'Use "/wordle command" to play as well.')
        return embed


    def render(self):
        padding = 5
        width = (self.square_size + padding) * self.word_length + padding
        height = (self.square_size + padding) * self.max_attempts + padding

        img = Image.new('RGB', (width, height), color=(49, 51, 57))
        fnt = ImageFont.truetype("bot/cogs/assets/fonts/arial.ttf", self.square_size - 6)
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

        img.save(f'/tmp/{self.ctx.author.id}_wordle.jpeg', format="JPEG")

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

        output = f"{self.ctx.author.mention}\n"
        output += f"{today.day} / {today.month} +{self.nth}\n\n"
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
        if os.path.exists(f'/tmp/{self.ctx.author.id}_wordle.jpeg'):
            os.remove(f'/tmp/{self.ctx.author.id}_wordle.jpeg')

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
    WORDS = sorted(map(str.upper, english_words_lower_alpha_set))

    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        self.scores = defaultdict(int)

        self.reset_wordle.start()
        self.today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    @commands.slash_command(guild_ids=[guild.id for guild in Config.guilds], description="Play wordle on Discord")
    async def wordle(self, ctx):
        if (ctx.author.id in self.games and
            not self.games[ctx.author.id].did_win() and
            not self.games[ctx.author.id].controls.is_finished()):

            game = self.games[ctx.author.id]
            await ctx.send("A game is already running", embed=game.to_embed(), ephemeral=True)
            return

        if ctx.author.id in self.games and self.games[ctx.author.id].did_win():
            self.scores[( self.today, ctx.user.id)] += 1

        self.games[ctx.author.id] = GameInstance(ctx,
                                                 words=self.WORDS,
                                                 nth=self.scores.get((self.today, ctx.author.id), 0))
        game = self.games[ctx.author.id]
        await game.start()

    @commands.command(name="wordle")
    async def wordle_help(self, ctx):
        """
        Guess the **WORDLE** in six tries.

        Each guess must be a valid five-letter word. Hit the submit button to validate the word.

        After each guess, the color of the tiles will change to show how close your guess was to the word.

        🟩 - the letter is at the correct place
        🟥 - the letter is not in the word
        🟨 - the letter is in the word, but at the wrong place

        Play the game using `/wordle`
        """

        await ctx.reply("👉 /wordle")

    @tasks.loop(minutes=30)
    async def reset_wordle(self):
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if today == self.today:
            return

        self.today = today

        seed = 0b01110111011011110111001001100100011011000110010100001010 + today.day + today.month * 31
        random.seed(seed)
        random.shuffle(self.WORDS)

        self.scores = {}
        for (user, game) in self.games.items():
            if game.did_win():
                self.scores[(today, user)] += 1

def setup(bot):
    bot.add_cog(Wordle(bot))
