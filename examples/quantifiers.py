#!/usr/bin/env python3
from speccer import *
from typing import T, List

def is_sorted(xs: List[T]) -> bool:
    '''Returns True if 'xs' is sorted ascending, O(nlgn)
    '''
    return list(sorted(xs)) == xs

def prop_sorted(context):
    '''A sorted list of length 2 exists
    '''
    return exists(List[int], 
            lambda xs: context.assertThat(is_sorted, xs) and context.assertEqual(len(xs), 2))

def prop_nested(_):
    return forall(List[int],
            lambda xs: forall(int,
                lambda y: y in xs))


if __name__ == '__main__':
    spec(3, prop_nested)

'''
Sample Output:

>> spec(3, prop_sorted)
...*
----------------------------------------
Found witness after 4 call(s)
In Property `prop_sorted`
----------------------------------------
Found Witness:
prop_sorted::EXISTS(List[int]) ->
 xs=[0, 0]

Reason:
> prop_sorted::EXISTS(List[int]), assert        is_sorted([0, 0])
> prop_sorted::EXISTS(List[int]), assert        2 == 2

 `prop_sorted` returned true

OK.
'''

'''
Sample Output:

>> spec(3, prop_nested)
E
========================================
Failure after 1 call(s)
In Property `prop_nested`
----------------------------------------
Found Counterexample:
prop_nested::FORALL(List[int]) ->
 xs=[]

prop_nested::FORALL(List[int]):FORALL(int) ->
 y=0

Reason:
 prop_nested::FORALL(List[int]):FORALL(int) property returned `False`

FAIL.
'''
