import string

from .strategy import *

LETTERS = string.ascii_lowercase

class IntStrat(Strategy[int]):
    def generate(self, depth, partial=0):
        if depth == 0:
            yield 1, [0]
        else:
            yield partial+1, [partial, -partial]

class StrStrat(Strategy[str]):
    def generate(self, depth, partial=''):
        m = min(depth, len(LETTERS))

        for k in LETTERS[:m]:
            s = partial + k
            yield s, [s]

try:
    import typing
except:
    pass
else:
    class ListStrat(Strategy[typing.List[typing.T]]):
        def generate(self, depth, t, partial=[]):
            # start with no values and then empty list
            if depth == 0:
                yield [], []
            elif depth == 1:
                yield [], [[]]
            else:
                for v in self.cons(Strategy[t]):
                    yield partial+[v], [partial+[v]]
        

# DEBUG
if False:
    class SimpleIntStrat(IntStrat):
        def generate(self, depth, partial=0):
            yield None, [1]

