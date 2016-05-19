#!/usr/bin/env python3
from speccer import *
from typing import T, List

def is_sorted(xs: List[T]) -> bool:
    '''Returns True if 'xs' is sorted ascending, O(nlgn)
    '''
    return list(sorted(xs)) == xs

# here the implication is a decorator since it changes the way List[int]'s are generated
# but the forall just quantifies over the generated List[int]'s without changing how
# they are generated
class ThisPropSet(PropertySet):
    def prop_exists_is_sorted(self):
        return exists(List[int], is_sorted)

    def prop_contain_2(self):
        return exists(List[int], lambda xs: 2 in xs)

if __name__ == '__main__':
    spec(3, ThisPropSet())
