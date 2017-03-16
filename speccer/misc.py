import os
import inspect
import collections

def get_stack_path(i=0, depth=None):
    '''Inspect Stack to get a relative name for this code point
    '''
    stk = inspect.stack()[(2 + i):depth]
    loc = []

    for sf in reversed(stk):
        _, fn = os.path.split(sf.filename)
        f = sf.function
        loc.append('[{}]{}'.format(fn, f))

    return ':'.join(loc)


def intersperse(its):
    iters = collections.deque(iter(i) for i in its)
    N = len(iters)
    idxs = collections.deque(range(N))
    rets = [None] * N
    while iters:
        try:
            i = iters.popleft()
            idx = idxs.popleft()
            yield next(i)
            idxs.append(idx)
            iters.append(i)
        except StopIteration as e:
            rets[idx] = e.value

    return tuple(rets)
