
from typing import Callable, Generator, List, Sequence, Tuple, TypeVar


T = TypeVar('T')
C = TypeVar('C')



def partition(cond: Callable[[T], bool], lst: List[T]) -> Tuple[List[T], List[T]]:
    return ([i for i in lst if cond(i)], [i for i in lst if not cond(i)])



def chunks(lst: List[T] | str, n: int) -> Generator[Sequence[T] | Sequence[str], None, None]:
    for i in range(0, len(lst), n):
        yield lst[i:i + n]