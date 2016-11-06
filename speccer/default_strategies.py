import string
try:
    from typing import Tuple, List, T
except ImportError:
    print('E: Cannot locate `typing`')
    print('E: Expected Python3.5 or greater')
    import sys
    sys.exit(1)

import logging
from .strategy import Strategy, mapS
from .utils import intersperse
from . import strategy

__all__ = [
    'Nat',
]

LETTERS = string.ascii_lowercase
log = logging.getLogger('default_strategies')

class Nat:
    pass

class NatStrat(Strategy[Nat]):
    def generate(self, depth):
        for i in range(depth):
            yield i

class IntStrat(Strategy[int]):
    def generate(self, depth):
        yield 0

        for i in range(1, 1 + depth):
            yield i
            yield -i

class ListStrat(Strategy[List]):
    def generate(self, depth, t):
        yield []

        def _list(x):
            for l in Strategy[List[t]](depth - 1):
                yield [x] + l

        yield from intersperse(*[_list(x) for x in Strategy[t](depth)])

class TupleStrat(Strategy[Tuple]):
    def generate(self, depth, *ts):
        yield from strategy.value_args(depth, *ts)

class StrStrat(Strategy[str]):
    def generate(self, depth):
        m = min(depth + 1, len(LETTERS))
        yield from LETTERS[:m]

class BoolStrat(Strategy[bool]):
    def generate(self, _):
        yield False
        yield True

# for debugging
if False:
    class SimpleIntStrat(IntStrat):
        def generate(self, depth):
            yield 0
            yield 1
