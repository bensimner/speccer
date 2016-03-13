import string

from .strategy import *

LETTERS = string.ascii_lowercase

class IntStrat(Strategy[int]):
    def generate(self, depth, partial=0, max_depth=0):
        if depth == 0:
            yield 1, [0]
        else:
            yield partial+1, [partial, -partial]

class StrStrat(Strategy[str]):
    def generate(self, depth, partial='', max_depth=0):
        m = min(max_depth, len(LETTERS))

        for k in LETTERS[:m]:
            s = partial + k
            yield s, [s]

@map_strategy(float, Strategy[int])
def OtherIntStrat(d, i, max_depth=0):
    yield i

try:
    import typing
except:
    pass
else:
    class ListStrat(Strategy[typing.List]):
        def generate(self, depth, t, partial=[], max_depth=0):
            # start with empty list
            if depth == 0:
                yield [], [[]]
            else:
                for v in values(depth, t):
                    yield partial+[v], [partial+[v]]
