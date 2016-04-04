#!/usr/bin/env python3
from speccer import *
from typing import T, List

def is_sorted(xs: List[T]) -> bool:
    '''Returns True if 'xs' is sorted ascending, O(nlgn)
    '''
    return list(sorted(xs)) == xs

def prop_sorted():
    '''A sorted list of length 2 exists
    '''
    return exists(List[int],
            lambda xs: is_sorted(xs) and len(xs) == 2)

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
 `prop_sorted` returned true

OK.
'''
