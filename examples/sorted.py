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
@implication(is_sorted)
def prop_sorted():
    return forall(List[int], is_sorted)

if __name__ == '__main__':
    spec(3, prop_sorted())

'''
Sample Output:

...............
----------------------------------------
Ran to 15 calls
Found no counterexample to depth 3
15/15

OK
'''
