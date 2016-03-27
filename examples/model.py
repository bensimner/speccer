#!/usr/bin/env python3
import functools
import collections
import operator

from speccer import *

class Q:
    def __init__(self, n):
        self._size = n
        self._lp = 0
        self._rp = 0
        self._array = [0] * self._size

    def enq(self, v):
        self._array[self._rp] = v
        self._rp = (self._rp + 1) % self._size

    def deq(self):
        v = self._array[self._lp]
        self._rp = (self._rp + 1) % self._size
        return v

    def size(self):
        return self._rp - self._lp

MyModel_state = collections.namedtuple('MyModel_state', ['array', 'size'])

def MyModel_initial_state():
    return MyModel_state(None, -1)

def MyModel_is_valid(cmds):
    return is_valid(cmds, initial=MyModel_initial_state)

class MyModel(Model):
    @command()
    def new(n: int) -> Q:
        return Q(n)

    @new.pre
    def new(state, args):
        ptr, n = state
        assertIs(ptr, None)

    @new.next
    def new(state, args, v):
        n, = args
        return MyModel_state([], n)

    @new.post
    def new(state, args, q):
        n, = args
        # ensure that a new queue has right size
        assertEqual(n, q._size)

    @command()
    def put(q: Q, n: int) -> None:
        q.enq(n)

    @put.pre
    def put(state, args):
        q, n = args
        arr, sz = state
        assertIsNot(q, None)
        assertTrue(len(arr) < sz)

    @put.next
    def put(state, args, v):
        # the list within is mutable
        state.array.append(v)
        return state

    @command()
    def get(q: Q) -> int:
        return q.deq()

    @get.pre
    def get(state, args):
        arr, sz = state
        q, = args
        assertTrue(len(arr) > 0)

    @get.next
    def get(state, args, v):
        state.array[:] = state.array[1:]
        return state
    
    @command()
    def size(q: Q) -> int:
        return q.size()

    @size.post
    def size(state, args, size):
        arr, _ = state
        assertEqual(size, len(arr)) 

# TODO: Some separation between validation on implication and actually running the code
# also, show failures based on pre/post condition and have return values shown etc
@implication(MyModel_is_valid)
@Property
def prop_model(cmds: MyModel):
    '''All programs are limited in size
    (hopefully! false)
    '''
    assertThat(operator.lt, len(list(cmds)), 3)

if __name__ == '__main__':
    spec(4, prop_model)

'''
Sample Output:

.......E
========================================
Failure after 8 calls (104 did not meet implication)
In Property `prop_model`
----------------------------------------
Found Counterexample:
> a = new(1)
> put(a, 0)
> get(a)

Reason:
 f(3, 3) is false
'''
