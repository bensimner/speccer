from .model import *
from .strategy import *
from .spec import *

from . import default_strategies

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
    def new(self, args):
        '''Can only `new(n)` on n > 0,
        and `new` hasn't been called before
        '''
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

    @enqueue.pre
    def enqueue(self, args):
        '''enqueue on a Q is always valid
        '''
        q, v = args
        self.assertEqual(type(q), Q)


    @enqueue.next
    def enqueue(self, args):
        q, v = args
        ptr, sz, l = self.state
        return queue_state(ptr, size, l + [v])

    @enqueue.post
    def enqueue(self):
        pass

    @command
    def dequeue(self, q: Q) -> int:
        return q.deq()

@Property
def prop_queueWorks(model: QueueModel):
    validate(model)

print('-----------------')
print('-----------------')
vals = list(QueueModel.__partial_strat__.values(3))
for cmds in vals:
    print('----')
    for cmd in cmds:
        print(pretty_str(cmd))
