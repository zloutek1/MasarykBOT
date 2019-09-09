import sys
import discord.utils


class GetModule(sys.modules[__name__].__class__):
    def __call__(self, iterable, **attrs):
        result = []
        for item in iterable:
            matches = True
            for attr, val in attrs.items():
                if attr == "key" and isinstance(val, type(lambda: 0)):
                    matches &= val(item)
                elif isinstance(item, dict):
                    matches &= item.get(attr) == val
                else:
                    matches &= getattr(item, attr) == val
            if matches:
                result.append(item)

        if len(result) == 0:
            return None
        if len(result) == 1:
            return result[0]
        return result


sys.modules[__name__].__class__ = GetModule
