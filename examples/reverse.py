import logging.config

from speccer import *
from typing import List

def is_sorted(xs: List[int]) -> bool:
    # sorted either way
    return list(sorted(xs)) == xs or list(reversed(sorted(xs))) == xs

@Property
def prop_sortedReversed(xs: List[int]):
    '''a List of int's is sorted when reversed

    (obviously False, to test output)
    '''
    assertThat(is_sorted, list(reversed(xs)))

if __name__ == '__main__':
    spec(3, prop_sortedReversed)

