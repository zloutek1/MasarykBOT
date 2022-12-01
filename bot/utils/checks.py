import functools

import aioredis
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



class RedisRequiredException(RuntimeError):
    pass



def requires_redis(func):
    # noinspection PyProtectedMember
    redis_available = aioredis.Redis in inject.get_injector()._bindings
    if not redis_available:
        raise RedisRequiredException


    @functools.wraps(func)
    async def wrapper(bot):
        return await func(bot)


    return wrapper
