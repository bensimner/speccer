from speccer import *
from typing import List

def is_sorted(xs: List[int]) -> bool:
    x, y = None, None
    for a in xs:
        if x and y and x > y:
            return False
        x, y = y, a
    return True

@Property
def prop_sortedReversed(xs: List[int]):
    '''a List of int's is sorted when reversed

    (obviously False, to test output)
    '''
    assertThat(is_sorted, list(reversed(xs)))

if __name__ == '__main__':
    spec(3, prop_sortedReversed)

