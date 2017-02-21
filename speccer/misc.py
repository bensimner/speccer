import collections

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
