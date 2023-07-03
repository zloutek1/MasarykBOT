import abc
import logging
from typing import NamedTuple, Generic, TypeVar

import discord

from core.context.__init__ import Context

log = logging.getLogger(__name__)
T = TypeVar('T')


class Diff(NamedTuple, Generic[T]):
    created: set[T]
    updated: set[T]
    deleted: set[T]


class Syncer(abc.ABC, Generic[T]):
    """Base class for synchronising the database with objects in the Discord cache."""

    @staticmethod
    @abc.abstractmethod
    def name() -> str:
        """The name of the syncer; used in output messages and logging."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def _get_diff(self, guild: discord.Guild) -> Diff[T]:
        """Return the difference between the cache of `guild` and the database."""
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def _sync(self, diff: Diff[T]) -> None:
        """Perform the API calls for synchronisation."""
        raise NotImplementedError  # pragma: no cover

    async def sync(self, guild: discord.Guild, ctx: Context | None = None) -> None:
        """
        Synchronise the database with the cache of `guild`.

        If `ctx` is given, send a message with the results.
        """
        log.info(f"Starting {self.name} syncer.")

        if ctx:
            message = await ctx.send(f"📊 Synchronising {self.name}s.")
        else:
            message = None
        diff = await self._get_diff(guild)

        try:
            await self._sync(diff)
        except Exception as e:
            log.exception(f"{self.name} syncer failed!")

            # Don't show response text because it's probably some really long HTML.
            results = f"```{str(e) or 'See log output for details'}```"
            content = f":x: Synchronisation of {self.name}s failed: {results}"
        else:
            diff_dict = diff._asdict()
            results = (f"{name} `{len(val)}`" for name, val in diff_dict.items() if val is not None)
            results = ", ".join(results)

            log.info(f"{self.name} syncer finished: {results}.")
            content = f":ok_hand: Synchronisation of {self.name}s complete: {results}"

        if message:
            await message.edit(content=content)
