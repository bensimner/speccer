import string

from .strategy import *

LETTERS = string.ascii_lowercase

class IntStrat(Strategy[int]):
    def generate(self, depth, partial=0, max_depth=0):
        yield None, [0]

        for k in range(1, max_depth):
            yield None, [k, -k]


class StrStrat(Strategy[str]):
    def generate(self, depth, partial='', max_depth=0):
        m = min(max_depth, len(LETTERS))

        for k in LETTERS[:m]:
            s = partial + k
            yield s, [s]

@map_strategy(None, IntStrat)
def OtherIntStrat(d, i):
    yield i
