#!/usr/bin/env python3
from speccer import *
from typing import T, List

def is_sorted(xs: List[T]) -> bool:
    '''Returns True if 'xs' is sorted ascending, O(nlgn)
    '''
    return list(sorted(xs)) == xs

@Property
def prop_sortedReversed(xs: List[int]):
    '''a List of int's is sorted when reversed

    (obviously False, to test output)
    '''
    assertThat(is_sorted, list(reversed(xs)))

if __name__ == '__main__':
    spec(2, prop_sortedReversed)

'''
Sample Output:

.....E
========================================
Failure after 6 calls
In Property `prop_sortedReversed`
----------------------------------------
Found Counterexample:
 ([0, 1],)

Reason:
 is_sorted([1, 0]) is false
'''
