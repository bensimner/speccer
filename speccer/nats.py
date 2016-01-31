# strategy.py - Strategies for producing arguments to model commands
# author: Ben Simner 

from strategy import *

class Nat:
    def __init__(self, suc):
        self.suc = suc

    def __repr__(self):
        if self.suc == None:
            return 'Z'
        else:
            return repr(self.suc) + '+'

    def to_int(self):
        if self == Z:
            return 0
        return 1 + self.suc.to_int()

    @staticmethod
    def from_int(i):
        if i == 0:
            return Z
        else:
            return S(Nat.from_int(i - 1))

Z = Nat(None)
S = lambda n: Nat(n)

class NatS(Strategy[Nat]):
    def generate(depth, partial=0):
        k = Nat.from_int(partial)
        yield partial+1, [k]

@map_strategy(int, Strategy[Nat])
def IntStrat(nat):
    def nat_to_int(n):
        if n.suc is None:
            return 0
        return 1 + nat_to_int(n.suc)

    yield nat_to_int(nat)
    yield - nat_to_int(nat)

# generat partial = generate(int, ...)
print(list(values(Nat, 5)))
print(list(values(int, 3)))
