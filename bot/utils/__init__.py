from typing import Callable, Generator, List, Sequence, Tuple, TypeVar, AsyncIterator

from .discord_limit import *
from .checks import *
from .context import *
from .emoji import *
from .extra_types import *
from .logging import *


_T = TypeVar('_T')


def partition(cond: Callable[[_T], bool], lst: List[_T]) -> Tuple[List[_T], List[_T]]:
    """ split list on condition into (True, False) parts """
    return [i for i in lst if cond(i)], [i for i in lst if not cond(i)]


def chunks(lst: List[_T] | str, n: int) -> Generator[Sequence[_T] | Sequence[str], None, None]:
    """ split iterable into chunks of size n """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def map_range(x: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """ remap value from one range to another range """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def right_justify(text: str, by: int = 0, pad: str = " ") -> str:
    """ str.rjust accepting multiple characters """
    return pad * (by - len(str(text))) + str(text)


class EmptyAsyncIterator(AsyncIterator[_T]):
    def __aiter__(self) -> "AsyncIterator[_T]":
        return self

    async def __anext__(self) -> _T:
        raise StopAsyncIteration


def sanitize_channel_name(channel_name: str) -> str:
    """keep special characters in channel name"""

    words = (channel_name.lower()
             .replace("-", "–")
             .split())

    return ("-".join(words)
            .replace("+", "﹢")
            .replace(".", "․")
            .replace(",", "")
            .replace("#", "＃")
            .replace("/", "／")
            .replace("(", "")
            .replace(")", "")
            .replace(":", "꞉")
            .replace("?", "？"))
