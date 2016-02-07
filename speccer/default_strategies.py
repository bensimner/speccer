import string

from strategy import *

LETTERS = string.ascii_lowercase

class Nat(int):
    pass

class IntStrat(Strategy[int]):
    def generate(depth, max_depth, partial=0):
        yield None, [0]

        for k in range(1, max_depth):
            yield None, [k, -k]

class NatStrat(Strategy[Nat]):
    def generate(depth, max_depth, partial=0):
        for k in range(max_depth):
            yield None, [Nat(k)]



class StrStrat(Strategy[str]):
    def generate(depth, partial='', max_depth=0):
        m = min(max_depth, len(LETTERS))

        for k in LETTERS[:m]:
            s = partial + k
            yield s, [s]

@map_strategy(None, IntStrat)
def OtherIntStrat(d, i):
    yield i

if __name__ == '__main__':
    print(list(values(Nat, 2)))
