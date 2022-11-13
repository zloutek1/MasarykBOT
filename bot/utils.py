
from typing import Callable, Generator, List, Sequence, Tuple, TypeVar
import discord


T = TypeVar('T')
C = TypeVar('C')


def partition(cond: Callable[[T], bool], lst: List[T]) -> Tuple[List[T], List[T]]:
    """ split list on condition into (True, False) parts """
    return ([i for i in lst if cond(i)], [i for i in lst if not cond(i)])


def chunks(lst: List[T] | str, n: int) -> Generator[Sequence[T] | Sequence[str], None, None]:
    """ split iterable into chunks of size n """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def map_range(x: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """ remap value from one range to another range """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def right_justify(text: str, by: int = 0, pad:str = " ") -> str:
    """ str.rjust accepting multiple characters """
    return pad * (by - len(str(text))) + str(text)


def emoji_name(emoji: discord.Emoji | discord.PartialEmoji | str) -> str:
    if isinstance(emoji, str):
        return emoji
    return emoji.name