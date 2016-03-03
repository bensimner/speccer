import string

from .strategy import *

LETTERS = string.ascii_lowercase

class IntStrat(Strategy[int]):
    def generate(self, depth, partial=0, max_depth=0):
        yield None, [0]

        for k in range(1, max_depth):
            yield None, [k, -k]

# overwrite the IntStrat to only generate [1] when asked
class TestIntStrat(Strategy[int]):
    def generate(self, depth, partial=0, max_depth=0):
        yield None, [1]

class StrStrat(Strategy[str]):
    def generate(self, depth, partial='', max_depth=0):
        m = min(max_depth, len(LETTERS))

        for k in LETTERS[:m]:
            s = partial + k
            yield s, [s]

@map_strategy(float, Strategy[int])
def OtherIntStrat(d, i, max_depth=0):
    yield i
