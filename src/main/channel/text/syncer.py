import logging

import discord

from channel.text.model import TextChannel
from channel.text.repository import TextChannelRepository
from sync.syncer import Syncer, Diff

log = logging.getLogger(__name__)


class TextChannelSyncer(Syncer[TextChannel]):
    """Synchronise the database with text channels in the cache."""

    name = "text_channel"

    def __init__(self, repository: TextChannelRepository):
        self.repository = repository

    async def _get_diff(self, guild: discord.Guild) -> Diff:
        """Return the difference of text channels between the cache of `guild` and the database."""
        log.debug("Getting the diff for text channels.")

        db_text_channels = set(await self.repository.find_all())
        guild_text_channels: set[TextChannel] = {TextChannel.from_discord(text_channel)
                                                 for text_channel in guild.text_channels}

        text_channels_to_create = guild_text_channels - db_text_channels
        text_channels_to_update = guild_text_channels - text_channels_to_create
        text_channels_to_delete = db_text_channels - guild_text_channels

        return Diff(text_channels_to_create, text_channels_to_update, text_channels_to_delete)

    async def _sync(self, diff: Diff[TextChannel]) -> None:
        """Synchronise the database with the text channels cache of `guild`."""
        log.debug("Syncing created text channels...")
        for text_channel in diff.created:
            await self.repository.create(text_channel)

        log.debug("Syncing updated text channels...")
        for text_channel in diff.updated:
            await self.repository.update(text_channel)

        log.debug("Syncing deleted text channels...")
        for text_channel in diff.deleted:
            await self.repository.delete(text_channel.id)
