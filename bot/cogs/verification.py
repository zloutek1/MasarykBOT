import logging
from typing import cast

import discord
from discord.abc import Snowflake, Messageable
from discord.ext import commands
from discord.utils import get

from bot.constants import CONFIG

log = logging.getLogger(__name__)
E_MISSING_PERMISSIONS = 50013


class VerificationService:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def is_verification_channel(channel_id: int) -> bool:
        return channel_id in (guild.channels.verification for guild in CONFIG.guilds)

    def has_required_permissions(self, guild_id: int) -> bool:
        assert (guild := get(self.bot.guilds, id=guild_id))
        return guild.me.guild_permissions.manage_roles

    async def fetch_message(self, payload: discord.RawReactionActionEvent) -> discord.Message:
        channel = await self.bot.fetch_channel(payload.channel_id)
        if not isinstance(channel, Messageable):
            raise AssertionError(f"channel {channel} is not messageable")
        return await channel.fetch_message(payload.message_id)

    @staticmethod
    async def verify_member(member: discord.Member) -> None:
        assert (guild_config := get(CONFIG.guilds, id=member.guild.id))
        if not (verified_role := get(member.guild.roles, id=guild_config.roles.verified)):
            log.warning("No verified role present in guild %s", member.guild)
            return

        await member.add_roles(cast(Snowflake, verified_role))
        log.info("verified user %s, added role %s", member.name, f"@{verified_role}")

    @staticmethod
    async def unverify_member(member: discord.Member) -> None:
        assert (guild_config := get(CONFIG.guilds, id=member.guild.id))
        if not (verified_role := get(member.guild.roles, id=guild_config.roles.verified)):
            log.warning("No verified role present in guild %s", member.guild)
            return

        await member.remove_roles(cast(Snowflake, verified_role))
        log.info("unverified user %s, removed role %s", member.name, f"@{verified_role}")


class Verification(commands.Cog):
    def __init__(self, bot: commands.Bot, service: VerificationService = None) -> None:
        self.bot = bot
        self.service = service or VerificationService(bot)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        pass
        # await self._synchronize()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        await self.on_raw_reaction_update(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        await self.on_raw_reaction_update(payload)

    async def on_raw_reaction_update(self, payload: discord.RawReactionActionEvent) -> None:
        if not self.service.is_verification_channel(payload.channel_id):
            return

        if payload.emoji.id != CONFIG.emoji.Verification:
            return

        if not self.service.has_required_permissions(payload.guild_id):
            log.warning("I don't have required permissions in guid with id %d", payload.guild_id)
            return

        message = await self.service.fetch_message(payload)
        member = await message.guild.fetch_member(payload.user_id)

        if payload.event_type == "REACTION_ADD":
            await self.service.verify_member(member)
        elif payload.event_type == "REACTION_REMOVE":
            await self.service.unverify_member(member)
        else:
            raise NotImplementedError

    # TODO: implement balancing


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Verification(bot))
