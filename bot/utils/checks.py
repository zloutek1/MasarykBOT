import functools

import inject



class DatabaseRequiredException(RuntimeError):
    pass



def requires_database(func):
    from bot.db import Pool

    # noinspection PyProtectedMember
    database_available = Pool in inject.get_injector()._bindings
    if not database_available:
        raise DatabaseRequiredException


    @functools.wraps(func)
    async def wrapper(bot):
        return await func(bot)


    return wrapper
