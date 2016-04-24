import string
try:
    from typing import Tuple, List, T
except ImportError:
    print('E: Cannot locate `typing`')
    print('E: Expected Python3.5 or greater')
    import sys
    sys.exit(1)

import logging
from .strategy import *
from . import strategy

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

        for i in range(1, 1+depth):
            yield i
            yield -i

class ListStrat(Strategy[List[T]]):
    def generate(self, depth, t):
        def mk_list(a: t, b: List[t]) -> List[t]:
            return [a] + b

        yield []
        yield from self.cons(mk_list)

class TupleStrat(Strategy[Tuple]):
    def generate(self, depth, *ts):
        yield from strategy.value_args(depth, *ts)
    
class StrStrat(Strategy[str]):
    def generate(self, depth):
        m = min(depth + 1, len(LETTERS))
        yield from LETTERS[:m]

# for debugging
if False:
    class SimpleIntStrat(IntStrat):
        def generate(self, depth):
            yield 0
            yield 1
