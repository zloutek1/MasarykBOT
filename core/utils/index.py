import sys
import discord.utils


class IndexModule(sys.modules[__name__].__class__):
    def __call__(self, iterable, **attrs):
        result = list(map(lambda item: item[0], filter(lambda item: all(
            (
                hasattr(item[1], attr) and
                getattr(item[1], attr) == attrs[attr]
            ) or (
                isinstance(item[1], dict) and
                attr in item[1] and item[1][attr] == attrs[attr]
            ) for attr in attrs), enumerate(iterable))))
        return (result if len(result) > 1 else
                result[0] if len(result) == 1 else
                None)


sys.modules[__name__].__class__ = IndexModule
