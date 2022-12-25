import functools
from typing import TYPE_CHECKING, Awaitable, Callable, TypeVar

import inject
from discord.ext import commands
    


_T = TypeVar('_T')


class DatabaseRequiredException(RuntimeError):
    pass



def requires_database(func: Callable[..., Awaitable[_T]]) -> Callable[..., Awaitable[_T]]:
    @functools.wraps(func)
    async def wrapper(bot: commands.Bot) -> _T:
        injector = inject.get_injector()
        assert injector, "no dependecny injector provided"
        
        from bot.db import Pool
        database_available = Pool in injector._bindings # type: ignore[misc]
        if not database_available:
            raise DatabaseRequiredException

        return await func(bot)
    return wrapper
