import logging
from typing import cast, Dict

import discord
from discord.abc import Snowflake
from discord.ext import commands
from discord.utils import get

from bot.constants import CONFIG

log = logging.getLogger(__name__)
E_MISSING_PERMISSIONS = 50013


class VerificationService:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def load_verification_messages(self) -> Dict[int, discord.Message]:
        result = {}
        for guild_config in CONFIG.guilds:
            channel_id = guild_config.channels.verification
            if not (channel := self.bot.get_channel(channel_id)):
                continue
            message = await self._find_verification_message(channel)
            result[message.id] = message
        return result

    @staticmethod
    async def _find_verification_message(channel: discord.abc.Messageable) -> discord.Message:
        async for message in channel.history(oldest_first=True):
            for reaction in message.reactions:
                if reaction.emoji.id == CONFIG.emoji.Verification:
                    return message

    def has_required_permissions(self, guild_id: int) -> bool:
        assert (guild := get(self.bot.guilds, id=guild_id))
        return guild.me.guild_permissions.manage_roles

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
        self.verification_messages: Dict[int, discord.Message] = {}

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.verification_messages = await self.service.load_verification_messages()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if self._is_valid_payload(payload):
            await self.on_raw_reaction_update(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        if self._is_valid_payload(payload):
            await self.on_raw_reaction_update(payload)

    async def on_raw_reaction_update(self, payload: discord.RawReactionActionEvent) -> None:
        message = self.verification_messages[payload.message_id]
        member = await message.guild.fetch_member(payload.user_id)

        if payload.event_type == "REACTION_ADD":
            await self.service.verify_member(member)
        elif payload.event_type == "REACTION_REMOVE":
            await self.service.unverify_member(member)

    def _is_valid_payload(self, payload: discord.RawReactionActionEvent) -> bool:
        return (payload.message_id in self.verification_messages
                and payload.emoji.id == CONFIG.emoji.Verification
                and self.service.has_required_permissions(payload.guild_id))

    # TODO: implement balancing


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Verification(bot))
