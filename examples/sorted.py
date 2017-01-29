#!/usr/bin/env python3
from speccer import spec, forall
from typing import List

def is_sorted(xs):
    return xs == list(sorted(xs))

def prop_all_lists_are_sorted():
    return forall(List[int], is_sorted)

if __name__ == '__main__':
    spec(4, prop_all_lists_are_sorted)

'''
Sample Output:

....F
================================================================================
Failure
After 4 call(s) (0 did not meet implication)
To depth 4
In property `prop_all_lists_are_sorted`

prop_all_lists_are_sorted.FORALL(List[int]) ->
 counterexample:
  xs=[1, 0]

FAIL
'''
