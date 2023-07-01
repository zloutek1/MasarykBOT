import logging

import discord

from role.model import Role
from sync.syncer import Syncer, Diff

log = logging.getLogger(__name__)


class RoleSyncer(Syncer[Role]):
    """Synchronise the database with roles in the cache."""

    name = "role"

    @staticmethod
    async def _get_diff(guild: discord.Guild) -> Diff:
        """Return the difference of roles between the cache of `guild` and the database."""
        log.debug("Getting the diff for roles.")

        roles = []  # await bot.instance.api_client.get("bot/roles") # TODO: fetch roles
        db_roles = {Role(**role_dict) for role_dict in roles}

        guild_roles = {
            Role(
                discord_id=role.id,
                name=role.name,
            )
            for role in guild.roles
        }

        guild_role_ids = {role.discord_id for role in guild_roles}
        api_role_ids = {role.discord_id for role in db_roles}
        new_role_ids = guild_role_ids - api_role_ids
        deleted_role_ids = api_role_ids - guild_role_ids

        # New roles are those which are on the cached guild but not on the
        # DB guild, going by the role ID. We need to send them in for creation.
        roles_to_create = {role for role in guild_roles if role.discord_id in new_role_ids}
        roles_to_update = guild_roles - db_roles - roles_to_create
        roles_to_delete = {role for role in db_roles if role.discord_id in deleted_role_ids}

        return Diff(roles_to_create, roles_to_update, roles_to_delete)

    @staticmethod
    async def _sync(diff: Diff[Role]) -> None:
        """Synchronise the database with the role cache of `guild`."""
        log.debug("Syncing created roles...")
        for role in diff.created:
            pass  # await bot.instance.api_client.post("bot/roles", json=role._asdict())

        log.debug("Syncing updated roles...")
        for role in diff.updated:
            pass  # await bot.instance.api_client.put(f"bot/roles/{role.id}", json=role._asdict())

        log.debug("Syncing deleted roles...")
        for role in diff.deleted:
            pass  # await bot.instance.api_client.delete(f"bot/roles/{role.id}")
