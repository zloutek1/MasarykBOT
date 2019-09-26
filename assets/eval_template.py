import asyncio
import importlib


def __restricted_import__(name, globals=None, locals=None, fromlist=(), level=0):

    allowed = ("asyncio.events",
               'math', 'random', 'time', 'datetime',
               'functools', 'itertools', 'operator', 'string',
               'collections', 're', 'json',
               'heapq', 'bisect', 'copy', 'hashlib')

    frommodule = globals['__name__'] if globals else None

    if frommodule not in allowed and frommodule + "." + name not in allowed and name not in allowed:
        raise ImportError("module '%s.%s' is restricted." % (frommodule, name))

    return importlib.__import__(name, globals, locals, fromlist, level)


__builtins__.__dict__['__import__'] = __restricted_import__


async def func():
    global asyncio, importlib
    del asyncio
    del importlib
{body}

ret = asyncio.get_event_loop().run_until_complete(func())
if ret:
    print("returned:", ret)
