import asyncio

__all__ = ['future']


def future(value=None):
    """
    create a mock return value from an async function
    """
    f = asyncio.Future()
    f.set_result(value)
    return f
