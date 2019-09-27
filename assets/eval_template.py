import asyncio
import importlib as importlib
from PIL import Image
import io


def __restricted_import__(name, globals=None, locals=None, fromlist=(), level=0):

    ALLOWED_STDLIB_MODULE_IMPORTS = ('math', 'random', 'time', 'datetime',
                                     'functools', 'itertools', 'operator', 'string',
                                     'collections', 're', 'json',
                                     'heapq', 'bisect', 'copy', 'hashlib')
    OTHER_STDLIB_WHITELIST = ('StringIO', 'io', 'turtle')

    allowed = ALLOWED_STDLIB_MODULE_IMPORTS + OTHER_STDLIB_WHITELIST

    frommodule = globals.get('__name__', '__main__') if globals else None

    if frommodule not in allowed and frommodule + "." + name not in allowed and name not in allowed:
        raise ImportError("module '%s.%s' is restricted." % (frommodule, name))

    return importlib.__import__(name, globals, locals, fromlist, level)


def open_wrapper(*args):
    raise Exception('''open() is not supported by Python Tutor.
Instead use io.StringIO() to simulate a file.
Here is an example: http://goo.gl/uNvBGl''')


async def __func():
    user_builtins = {}

    builtin_items = []
    for k in dir(__builtins__):
        builtin_items.append((k, getattr(__builtins__, k)))

    for (k, v) in builtin_items:
        if k == 'open':  # put this before BANNED_BUILTINS
            user_builtins[k] = open_wrapper
        elif k == '__import__':
            user_builtins[k] = __restricted_import__
        else:
            if k == 'raw_input':
                pass
            elif k == 'input':
                pass
            else:
                user_builtins[k] = v

    user_globals = {"__name__": "__main__",
                    "__builtins__": user_builtins}

    exec("""
{{{body}}}
""", user_globals)

    if "turtle" in user_globals:
        turtle = user_globals.get("turtle")
        ts = turtle.getscreen()
        canvas = ts.getcanvas()

        ps = canvas.postscript(colormode='color')
        img = Image.open(io.BytesIO(ps.encode('utf-8')))
        img.save(f'{__file__}.jpg')


ret = asyncio.get_event_loop().run_until_complete(__func())
if ret:
    print("returned:", ret)
