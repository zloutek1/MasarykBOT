from typing import List, Dict

import discord
from discord.utils import escape_markdown

from bot.utils import right_justify
from bot.db.cogs import LeaderboardEntity


class LeaderboardEmbed(discord.Embed):
    def __init__(
        self,
        top10: List[LeaderboardEntity],
        around: List[LeaderboardEntity],
        medals: Dict[int | None, discord.Emoji],
        user: discord.Member
    ) -> None:
        super().__init__(color=0x53acf2)

        self.medals = medals
        self.user = user

        self.add_field(
            inline=False,
            name="Top 10",
            value=self.make_table(top10)
        )
        self.add_field(
            inline=False,
            name="Your position",
            value=self.make_table(around)
        )

    def make_table(self, rows: List[LeaderboardEntity]) -> str:
        if not rows:
            return "empty"
        align_digits = len(str(rows[0].sent_total))

        return self.restrict_length(
            "\n".join(
                self.display_row(row, align_digits, row.author_id == self.user.id)
                for row in rows
            )
        )

    def display_row(self, row: LeaderboardEntity, align_digits: int, bold: bool = False) -> str:
        medal = self.medals.get(row.row_no, self.medals[None])
        count = right_justify(str(row.sent_total), align_digits, "\u2063 ")
        user = escape_markdown(row.author)
        user = f'**{user}**' if bold else f'{user}'

        return f"`{row.row_no:0>2}.` {medal} `{count}` {user}"

    @staticmethod
    def restrict_length(string: str) -> str:
        while len(string) >= 1024:
            lines = string.split("\n")
            longest = max(((i, lines[i]) for i in range(len(lines))), key=lambda x: x[1])
            lines[longest[0]] = lines[longest[0]].rstrip("...")[:-1] + "..."
            string = "\n".join(lines)
        return string
