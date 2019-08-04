import asyncio
import requests

import discord
from discord.ext import commands
from discord import Colour, Embed, Member, Object, File
from discord.ext.commands import has_permissions

from datetime import datetime, timedelta

from core.utils.checks import needs_database


class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @needs_database
    @has_permissions(manage_messages=True)
    async def backup(self, ctx):
        await ctx.message.delete()

        guild = ctx.guild
        message = ctx.message
        ch = message.channel

        ctx.db.execute("DELETE FROM backup WHERE guild_id=%s", (guild.id,))
        ctx.db.execute("DELETE FROM backup_attachments WHERE guild_id=%s", (guild.id,))
        ctx.db.commit()

        message_batch = []
        attachment_batch = []

        async def get_channel_msg(channel):
            nonlocal message_batch, attachment_batch, messages_sent

            await asyncio.sleep(0)
            with requests.Session() as session:
                async for message in channel.history(limit=1000000):
                    message_batch.append((guild.id, channel.id, message.id, message.author.id, message.content, message.created_at))
                    messages_sent += 1

                    if len(message_batch) > 100:
                        ctx.db.executemany("INSERT INTO backup (guild_id, channel_id, message_id, author_id, content, `timestamp`) VALUES (%s, %s, %s, %s, %s, %s)", message_batch)
                        ctx.db.commit()
                        message_batch = []

                    # --- Atteachment
                    for attachment in message.attachments:
                        attachment_batch.append((guild.id, channel.id, message.id, message.author.id, attachment.size, attachment.filename, attachment.url, message.created_at))

                        if len(attachment_batch) > 100:
                            ctx.db.executemany("INSERT INTO backup_attachments (guild_id, channel_id, message_id, author_id, size, filename, url, `timestamp`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", attachment_batch)
                            ctx.db.commit()
                            attachment_batch = []

        for channel in guild.channels:
            messages_sent = 0

            if not type(channel) is discord.channel.TextChannel:
                continue

            try:
                task = await asyncio.ensure_future(get_channel_msg(channel))
                print(f"[Backup] - {guild} : {messages_sent: >8} messages saved : Saved {channel}")
            except discord.Forbidden:
                print("[Backup] -", guild, ": Forbidden", channel)

        if len(message_batch) > 0:
            ctx.db.executemany("INSERT INTO backup (guild_id, channel_id, message_id, author_id, content, `timestamp`) VALUES (%s, %s, %s, %s, %s, %s)", message_batch)

        if len(attachment_batch) > 0:
            ctx.db.executemany("INSERT INTO backup_attachments (guild_id, channel_id, message_id, author_id, size, filename, url, `timestamp`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", attachment_batch)
        ctx.db.commit()

        print("Backup done")


def setup(bot):
    bot.add_cog(Backup(bot))
    print("Cog loaded: Backup")
