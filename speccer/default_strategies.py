import string
import itertools
import logging
import collections

from .strategy import Strategy
from .misc import intersperse
from . import strategy
from . import ops
from . import types
from .helper import HAS_TYPING

LETTERS = string.ascii_lowercase
log = logging.getLogger('default_strategies')

class NatStrat(Strategy[types.Nat]):
    def generate(self, depth):
        for i in range(depth + 1):
            yield i

class IntStrat(Strategy[int]):
    def generate(self, depth):
        yield 0

        for i in range(1, depth + 1):
            yield i
            yield -i

class Word2Strat(Strategy[types.Word2]):
    def generate(self, depth):
        yield 0

        for i in range(1, min(depth, 2**2)):
            yield i

class Word4Strat(Strategy[types.Word4]):
    def generate(self, depth):
        yield 0

        for i in range(1, min(depth, 2**4)):
            yield i

class Word8Strat(Strategy[types.Word8]):
    def generate(self, depth):
        yield 0

        for i in range(1, min(depth, 2**8)):
            yield i

if HAS_TYPING:
    import typing

    class PermutationsStrat(Strategy[types.Permutations]):
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
        '''TODO: make generation less strict'''
        def generate(self, depth, t, *args, **kwargs):
            alls = list(Strategy[t](depth, *args, **kwargs))

            def all_of_size(n):
                yield from (set(p) for p in itertools.combinations(alls, n))

            yield from intersperse(all_of_size(n) for n in range(depth))

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

@ops.mapS(Strategy[types.Nat], register_type=types.Neg)
def MappedStrat(depth, value):
    yield -value
