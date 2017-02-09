from . import PyState

try:
    import typing
    PyState.has_typing = True
except ImportError:
    import warnings
    warnings.warn('Cannot locate `typing`, expected python3.5 or greater, defaulting to builtins only.')

import string
import logging
import collections


from .strategy import Strategy
from .misc import intersperse
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

if PyState.has_typing:
    class ListStrat(Strategy[typing.List]):
        def generate(self, depth, t):
            yield []

            def _list(x):
                for l in Strategy[typing.List[t]](depth - 1):
                    yield [x] + l

            yield from intersperse(_list(x) for x in Strategy[t](depth))

    class SetStrat(Strategy[typing.Set]):
        '''TODO: make generation less redundant'''
        def generate(self, depth, t):
            yield {}

            def _list(x):
                for l in Strategy[typing.Set[t]](depth - 1):
                    yield {x}.union(l)

            yield from intersperse(_list(x) for x in Strategy[t](depth))

    class TupleStrat(Strategy[typing.Tuple]):
        def generate(self, depth, *ts):
            yield from strategy.value_args(depth, *ts)

    class UnionStrat(Strategy[typing.Union]):
        def generate(self, depth, *ts):
            yield from intersperse(Strategy[t](depth) for t in ts)

class StrStrat(Strategy[str]):
    def generate(self, depth):
        m = min(depth + 1, len(LETTERS))
        yield from LETTERS[:m]

class BoolStrat(Strategy[bool]):
    def generate(self, _):
        yield False
        yield True

class NoneStrat(Strategy[None]):
    def generate(self, _):
        yield None

# for debugging
if False:
    class SimpleIntStrat(IntStrat):
        def generate(self, depth):
            yield 0
            yield 1
