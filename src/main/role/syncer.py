import logging

import discord

from role.model import Role
from role.repository import RoleRepository
from sync.syncer import Syncer, Diff

log = logging.getLogger(__name__)


class RoleSyncer(Syncer[Role]):
    """Synchronise the database with roles in the cache."""

    name = "role"

    def __init__(self, repository: RoleRepository):
        self.repository = repository

    async def _get_diff(self, guild: discord.Guild) -> Diff:
        """Return the difference of roles between the cache of `guild` and the database."""
        log.debug("Getting the diff for roles.")

        db_roles = set(await self.repository.find_all())
        discord_roles = {Role.from_discord(role) for role in guild.roles}

        # New roles are those which are on the cached guild but not on the
        # DB guild, going by the role ID. We need to send them in for creation.
        roles_to_create = discord_roles - db_roles

        roles_to_update = set()
        for discord_role in discord_roles - roles_to_create:
            for db_role in db_roles:
                if discord_role == db_role:
                    if not discord_role.equals(db_role):
                        roles_to_update.add(discord_role)
                    break

        roles_to_delete = db_roles - discord_roles

        return Diff(roles_to_create, roles_to_update, roles_to_delete)

    async def _sync(self, diff: Diff[Role]) -> None:
        """Synchronise the database with the role cache of `guild`."""
        log.debug("Syncing created roles...")
        for role in diff.created:
            await self.repository.create(role)

        log.debug("Syncing updated roles...")
        for role in diff.updated:
            await self.repository.update(role)

        log.debug("Syncing deleted roles...")
        for role in diff.deleted:
            await self.repository.delete(role.id)
