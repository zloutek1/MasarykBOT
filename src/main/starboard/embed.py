import datetime

import discord


class StarboardEmbed(discord.Embed):
    def __init__(self, message: discord.Message) -> None:
        super().__init__(color=0xFFDF00)
        assert isinstance(message.channel, (discord.TextChannel, discord.Thread))

        self._get_content(message)
        self._set_author(message)

        if message.embeds:
            self._set_embed(message)

        if message.attachments:
            self._set_attachment(message)

        cest = datetime.timezone(offset=datetime.timedelta(hours=+1))
        self.set_footer(text=message.created_at.astimezone(cest).strftime("%d.%m.%Y %H:%M"))

    def _set_embed(self, message):
        embed = message.embeds[0]
        if embed.type == "image":
            self.set_image(url=embed.url)
        else:
            self.add_field(name='Embed',
                           value=f'[{embed.title}]({embed.url})',
                           inline=False)

    def _set_attachment(self, message):
        attachment = message.attachments[0]
        if not attachment.is_spoiler() and attachment.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
            self.set_image(url=attachment.url)
        elif attachment.is_spoiler():
            self.add_field(name='Attachment',
                           value=f'||[{attachment.filename}]({attachment.url})||',
                           inline=False)
        else:
            self.add_field(name='Attachment',
                           value=f'[{attachment.filename}]({attachment.url})',
                           inline=False)

    def _set_author(self, message):
        if message.author.avatar:
            self.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
        else:
            self.set_author(name=message.author.display_name, icon_url=message.author.default_avatar.url)

    def _get_content(self, message):
        content = message.content
        reactions = self._format_reactions(message)
        return (
                f"{content}\n{reactions}\n" +
                f"[Jump to original!]({message.jump_url}) in {message.channel.mention}"
        )

    def _format_reactions(self, message: discord.Message) -> str:
        return " ".join(
            self._format_reaction(reaction)
            for reaction in message.reactions
        )

    @staticmethod
    def _format_reaction(reaction: discord.Reaction) -> str:
        if isinstance(reaction.emoji, str):
            return f"{reaction} {reaction.count}"
        return f"<:{reaction.emoji.name}:{reaction.emoji.id}> {reaction.count}"
