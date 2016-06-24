#!/usr/bin/env python3
import collections

from speccer import *

class Q:
    '''A Horribly broken Queue implementation
    '''
    def __init__(self, n):
        self._size = n + 1
        #self._size = n # broken
        self._lp = 0
        self._rp = 0
        self._array = [0] * self._size

    def enq(self, v):
        self._array[self._rp] = v
        self._rp = (self._rp + 1) % self._size

    def deq(self):
        v = self._array[self._lp]
        self._lp = (self._lp + 1) % self._size
        return v

    def count(self):
        '''Returns the number of elements in the Queue
        '''
        return self._rp - self._lp # that's not right...
        #return (self._rp - self._lp) % self._size

    def __repr__(self):
        return 'Q(_array={}, out={}, in={}, size={})'.format(self._array, self._lp, self._rp, self.count())

    def __str__(self):
        return 'Queue(size={n})'.format(n=self._size - 1)

State = collections.namedtuple('State', ['array', 'size'])

class MyModel(Model):
    # initial state
    _STATE = State(None, -1)

    @command
    def new(n: int) -> Q:
        return Q(n)

    def new_pre(self, args):
        ptr, _ = self.state
        n, = args
        assertIs(ptr, None)
        return n > 0

    def new_next(self, args, v):
        n, = args
        return State([], n)

    @command
    def put(q: Q, n: int) -> None:
        q.enq(n)

    def put_pre(self, args):
        arr, sz = self.state
        return len(arr) < sz

    def put_next(self, args, result):
        _, v = args
        return State(self.state.array + [v], self.state.size)

    @command
    def get(q: Q) -> int:
        return q.deq()

    def get_pre(self, args):
        arr, sz = self.state
        q, = args
        assertTrue(len(arr) > 0)

    def get_post(self, args, result):
        arr, _ = self.state
        assertEqual(arr[0], result)

    def get_next(self, args, result):
        return State(self.state.array[1:], self.state.size)

    @command
    def count(q: Q) -> int:
        return q.count()

    def count_post(self, args, size):
        arr, _ = self.state
        assertEqual(size, len(arr))

def prop_model():
    '''Just check that the queue matches the model
    '''
    return forall(
        implies(MyModel.validate_pre, MyModel.Commands),
        lambda cmds: cmds.validate())

if __name__ == '__main__':
    enableLogging(debug=False)
    out = spec(6, prop_model)

'''
Sample Output:

>> spec(6, prop_model) # with debug int strategy
........................................
..............................E
========================================
Failure after 71 call(s) (4809 did not meet implication)
In Property `prop_model`
----------------------------------------
Found Counterexample:
prop_model::FORALL(<class '__main__.MyModel'>_Commands) ->
cmds =
> a = new(1) -> Queue(size=1)
> put(a, 0) -> None
> get(a) -> 0
> put(a, 0) -> None
> count(a) -> -1

Reason:
 {count_postcondition}: -1 != 1

FAIL.
'''
