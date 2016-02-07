from model import *
from strategy import *

import default_strategies

queue_state = collections.namedtuple('QueueState', ['ptr', 'size', 'list'])

class Q:
    def __init__(self, n):
        self._q = [0] * n
        self._i = 0
        self._n = n

    def enq(self, v):
        self._q[self._i] = v
        self._i += 1

    def deq(self):
        self._i -= 1
        return self._q[self._i]

class QueueModel(Model):
    @command
    def new(self, size: int) -> Q:
        return Q(size)

    @new.pre
    def new(self):
        pass

    @new.pre
    def new(self, args):
        size, = args
        self.assertTrue(size > 0)
        self.assertEqual(self.state.ptr, None)

    @new.next
    def new(self, args, q):
        size, = args
        return queue_state(q, size, [])

    @command
    def enqueue(self, q: Q, v: int):
        return q.enq(v)

    @command
    def dequeue(self, q: Q) -> int:
        return q.deq()

print('-----------------')
print('-----------------')
vals = list(QueueModel.__partial_strat__.values(3))
for cmds in vals:
    print('----')
    for cmd in cmds:
        print(pretty_str(cmd))
