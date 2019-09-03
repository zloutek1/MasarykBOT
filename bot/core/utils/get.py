import sys
import discord.utils


class GetModule(sys.modules[__name__].__class__):
    def __call__(self, iterable, **attrs):
        result = list(filter(lambda item: all(
            (
                hasattr(item, attr) and
                getattr(item, attr) == attrs[attr]
            ) or (
                isinstance(item, dict) and
                attr in item and item[attr] == attrs[attr]
            ) for attr in attrs), iterable))
        return (result if len(result) > 1 else
                result[0] if len(result) == 1 else
                None)


sys.modules[__name__].__class__ = GetModule
