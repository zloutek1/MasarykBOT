import asyncio
import importlib
import pickle


def secure_importer(name, globals=None, locals=None, fromlist=(), level=0):

    allowed = ["asyncio.events", "time"]
    frommodule = globals['__name__'] if globals else None

    if frommodule not in allowed and frommodule + "." + name not in allowed and name not in allowed:
        raise ImportError("module '%s.%s' is restricted." % (frommodule, name))

    return importlib.__import__(name, globals, locals, fromlist, level)


__builtins__.__dict__['__import__'] = secure_importer


async def func():
{body}

ret = asyncio.get_event_loop().run_until_complete(func())
if ret:
    print("returned:", ret)
