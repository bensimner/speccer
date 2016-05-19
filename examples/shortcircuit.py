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
class MyPropertySet(PropertySet):
    def prop_sorted(self):
        def check(self, xs: List[int]):
            # the ideal behaviour of this would be to have the StopIteration go up into the List[int]
            # strategy where it stops this branch of list generation
            # (which should be all lists of form (xs : _)
            print('check', xs)
            with implication():
                self.assertThat(is_sorted, xs)

            print('pass')
            self.assertThat(is_sorted, xs)
        return forall(List[int], check)

if __name__ == '__main__':
    spec(4, MyPropertySet())

'''
Sample Output:

...............
----------------------------------------
Ran to 15 call(s) (6 did not meet implication)
Found no counterexample to depth 3
15/15

OK.
'''
