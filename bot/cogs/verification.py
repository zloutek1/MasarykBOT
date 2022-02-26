import logging
from typing import List, Set, cast

import disnake as discord
from bot.constants import Config
from disnake.abc import Snowflake
from disnake.errors import Forbidden
from disnake.ext import commands, tasks
from disnake.utils import find, get

log = logging.getLogger(__name__)
E_MISSING_PERMISSIONS = 50013


class Verification(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @property
    def verification_channels(self) -> List[discord.TextChannel]:
        verification_ids = [guild.channels.verification for guild in Config.guilds]
        return [
            channel
            for channel_id in verification_ids
            if (channel := self.bot.get_channel(channel_id)) is not None
            if isinstance(channel, discord.TextChannel)
        ]

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        log.info("found %d verification channels", len(self.verification_channels))

        await self._synchronize()

    @tasks.loop(hours = 168)  # 168 hours == 1 week
    async def _repeat_synchronize(self) -> None:
        await self._synchronize()

    async def _synchronize(self) -> None:
        def confirm_react(reaction: discord.Reaction) -> bool:
            if isinstance(reaction.emoji, str):
                return False
            return reaction.emoji.name.lower() in ("verification", "verify", "accept")

        for channel in self.verification_channels:
            async for message in channel.history():
                verif_react = find(confirm_react, message.reactions)
                if verif_react is None:
                    continue

                await self._synchronize_react(channel.guild, verif_react)

    async def _synchronize_react(self, guild: discord.Guild, verif_react: discord.Reaction) -> None:
        guild_config = get(Config.guilds, id=guild.id)
        if guild_config is None:
            log.warning("I don't have a config for guild %s", guild)
            return

        if not guild.me.guild_permissions.manage_roles:
            log.warning("I don't have manage_roles permissions in %s", guild)
            return

        verified_role = find(lambda role: role.id == guild_config.roles.verified, guild.roles)
        if verified_role is None:
            log.warning("No verified role presnt in guild %s", guild)
            return

        with_role = set(filter(lambda member: verified_role in member.roles, guild.members))
        verified = cast(Set[discord.Member],
                        set(await verif_react.users()
                                             .filter(lambda user: isinstance(user, discord.Member))
                                             .flatten()
                        )
        )

        out_of_sync = len(with_role - verified) + len(verified - with_role)
        log.info("found %d users out of sync", out_of_sync)

        try:
            for member in with_role - verified:
                await self._verify_leave(member)

            for member in verified - with_role:
                await self._verify_join(member)

        except Forbidden as err:
            if err.code == E_MISSING_PERMISSIONS:
                log.warning("missing permissions in guild %s", guild)


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        await self.on_raw_reaction_update(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent) -> None:
        await self.on_raw_reaction_update(payload)

    async def on_raw_reaction_update(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.guild_id is None:
            return

        if (guild_config := get(Config.guilds, id=payload.guild_id)) is None:
            return

        if payload.channel_id != guild_config.channels.verification:
            return

        if payload.emoji.name.lower() not in ("verification", "verify", "accept"):
            return

        guild = get(self.bot.guilds, id=payload.guild_id)
        if guild is None:
            return

        member = get(guild.members, id=payload.user_id)
        if member is None:
            return

        if not guild.me.guild_permissions.manage_roles:
            log.warning("I don't have manage_roles permissions in %s", guild)
            return

        if payload.event_type == "REACTION_ADD":
            await self._verify_join(member)

        elif payload.event_type == "REACTION_REMOVE":
            await self._verify_leave(member)

    async def _verify_join(self, member: discord.Member) -> None:
        guild_config = get(Config.guilds, id=member.guild.id)
        if guild_config is None:
            log.warning("I don't have a config for guild %s", member.guild)
            return

        if not isinstance(member, discord.Member):
            log.warning("user %s is not longer a member of a guild", member)
            return

        verified_role = find(lambda role: role.id == guild_config.roles.verified, member.guild.roles)
        if verified_role is None:
            log.warning("No verified role presnt in guild %s", member.guild)
            return

        await member.add_roles(cast(Snowflake, verified_role))
        log.info("verified user %s, added role %s", member.name, f"@{verified_role}")

    async def _verify_leave(self, member: discord.Member) -> None:
        guild_config = get(Config.guilds, id=member.guild.id)
        if guild_config is None:
            log.warning("I don't have a config for guild %s", member.guild)
            return

        if not isinstance(member, discord.Member):
            log.warning("user %s is not longer a member of a guild", member)
            return

        to_remove = list(filter(lambda role: role.id == guild_config.roles.verified, member.roles))
        to_remove_s = cast(List[Snowflake], to_remove)
        await member.remove_roles(*to_remove_s)

        removed_roles = ', '.join(map(lambda r: '@'+r.name, to_remove))
        log.info("unverified user %s, removed roles %s", member.name, removed_roles)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Verification(bot))
