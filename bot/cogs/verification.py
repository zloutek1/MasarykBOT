import logging

import discord
from discord.ext import commands
from discord.utils import get, find
from discord.errors import Forbidden

from bot.cogs.utils import constants


log = logging.getLogger(__name__)
E_MISSING_PERMISSIONS = 50013


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def verification_channels(self):
        return [
            channel
            for channel_id in constants.verification_channels
            if (channel := self.bot.get_channel(channel_id)) is not None
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        log.info("found %d verification channels", len(self.verification_channels))

        await self._synchronize()

    async def _synchronize(self):
        def confirm_react(reaction):
            return reaction.emoji.name.lower() in ("verification", "verify", "accept")

        for channel in self.verification_channels:
            async for message in channel.history():
                verif_react = find(confirm_react, message.reactions)
                if verif_react is None:
                    continue

                await self._synchronize_react(channel.guild, verif_react)

    async def _synchronize_react(self, guild, verif_react):
        if not guild.me.guild_permissions.manage_roles:
            log.warning("I don't have manage_roles permissions in %s", guild)
            return

        verified_role = find(lambda role: role.id in constants.verified_roles, guild.roles)
        if verified_role is None:
            log.warning("No verified role presnt in guild %s", guild)
            return

        with_role = set(filter(lambda member: verified_role in member.roles, guild.members))
        verified = set(await verif_react.users().flatten())

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
    async def on_raw_reaction_add(self, payload):
        await self.on_raw_reaction_update(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.on_raw_reaction_update(payload)

    async def on_raw_reaction_update(self, payload):
        if payload.channel_id not in constants.verification_channels:
            return

        if payload.emoji.name.lower() not in ("verification", "verify", "accept"):
            return

        guild = get(self.bot.guilds, id=payload.guild_id)
        member = get(guild.members, id=payload.user_id)

        if not guild.me.guild_permissions.manage_roles:
            log.warning("I don't have manage_roles permissions in %s", guild)
            return

        if payload.event_type == "REACTION_ADD":
            await self._verify_join(member)

        elif payload.event_type == "REACTION_REMOVE":
            await self._verify_leave(member)

    async def _verify_join(self, member):
        if not isinstance(member, discord.Member):
            log.warning("user %s is not longer a member of a guild", member)
            return

        verified_role = find(lambda role: role.id in constants.verified_roles, member.guild.roles)
        if verified_role is None:
            log.warning("No verified role presnt in guild %s", member.guild)
            return

        await member.add_roles(verified_role)
        log.info("verified user %s, added role %s", member.name, f"@{verified_role}")

    async def _verify_leave(self, member):
        if not isinstance(member, discord.Member):
            log.warning("user %s is not longer a member of a guild", member)
            return

        removable_roles = constants.verified_roles
        to_remove = list(filter(lambda role: role.id in removable_roles, member.roles))
        await member.remove_roles(*to_remove)
        removed_roles = ', '.join(map(lambda r: '@'+r.name, to_remove))
        log.info("unverified user %s, removed roles %s", member.name, removed_roles)


def setup(bot):
    bot.add_cog(Verification(bot))
