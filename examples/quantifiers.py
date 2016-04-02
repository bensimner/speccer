#!/usr/bin/env python3
from speccer import *
from typing import T, List

def is_sorted(xs: List[T]) -> bool:
    '''Returns True if 'xs' is sorted ascending, O(nlgn)
    '''
    return list(sorted(xs)) == xs

@Property.exists
def prop_sorted(xs: List[int]):
    '''A sorted list of length 2 exists
    '''
    assertThat(is_sorted, xs)
    return len(xs) == 2

if __name__ == '__main__':
    spec(3, prop_sorted)

'''
Sample Output:

...*
----------------------------------------
Found witness after 4 call(s)
In Property `prop_sorted`
----------------------------------------
Found Witness:
 [0, 0]

Reason:
 ¬{is_sorted([0, 0]) is false}
 `prop_sorted` returned true

OK.
'''
