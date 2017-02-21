from . import PyState

try:
    import typing
    PyState.has_typing = True
except ImportError:
    import warnings
    warnings.warn('Cannot locate `typing`, expected python3.5 or greater, defaulting to builtins only.')

import string
import itertools
import logging
import collections

from .strategy import Strategy
from .misc import intersperse
from . import strategy
from . import ops

__all__ = [
    'Nat',
    'Permutations',
]


LETTERS = string.ascii_lowercase
log = logging.getLogger('default_strategies')

class Nat:
    '''Natural numbers 0, 1, 2, ...
    '''

class NatStrat(Strategy[Nat]):
    def generate(self, depth):
        for i in range(depth + 1):
            yield i

class IntStrat(Strategy[int]):
    def generate(self, depth):
        yield 0

        for i in range(1, depth + 1):
            yield i
            yield -i

if PyState.has_typing:
    T = typing.T
    class Permutations(typing.Generic[T]):
        '''Lists of permutations of some type T
        '''

    class PermutationsStrat(Strategy[Permutations]):
        def generate(self, depth, t, *args, **kws):
            yield from itertools.permutations(Strategy[t](depth, *args, **kws))

    class ListStrat(Strategy[typing.List]):
        def generate(self, depth, t, *args, **kws):
            yield []

            def _list(x):
                for l in Strategy[typing.List[t]](depth - 1, *args, **kws):
                    yield [x] + l

            yield from intersperse(_list(x) for x in Strategy[t](depth, *args, **kws))

    class SetStrat(Strategy[typing.Set]):
        '''TODO: make generation less redundant'''
        def generate(self, depth, t, *args, **kwargs):
            yield {}

            def _list(x):
                for l in Strategy[typing.Set[t]](depth - 1, *args, **kwargs):
                    yield {x}.union(l)

            yield from intersperse(_list(x) for x in Strategy[t](depth, *args, **kwargs))

    class TupleStrat(Strategy[typing.Tuple]):
        def generate(self, depth, *ts, **kwargs):
            yield from ops.value_args(depth, *ts, **kwargs)

    class UnionStrat(Strategy[typing.Union]):
        def generate(self, depth, *ts, **kwargs):
            yield from intersperse(Strategy[t](depth, **kwargs) for t in ts)

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


class Neg:
    pass

@ops.mapS(Strategy[Nat], register_type=Neg)
def MappedStrat(depth, value):
    yield -value

# for debugging
if False:
    class SimpleIntStrat(IntStrat):
        def generate(self, depth):
            yield 0
            yield 1
