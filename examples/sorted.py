#!/usr/bin/env python3
from speccer import *
from typing import T, List

def is_sorted(xs: List[T]) -> bool:
    '''Returns True if 'xs' is sorted ascending, O(nlgn)
    '''
    return list(sorted(xs)) == xs

@implication(is_sorted)
@Property
def prop_sorted(xs: List[int]):
    '''A sorted list is sorted
    '''
    assertThat(is_sorted, xs)

if __name__ == '__main__':
    spec(3, prop_sorted)

'''
Sample Output:

...............
----------------------------------------
Ran to 15 calls
Found no counterexample to depth 3
15/15

OK
'''
