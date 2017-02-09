import collections

from . import PyState
if PyState.has_typing:
    import typing

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

def convert_type(t):
    '''Converts a python type to a `typing` type
    '''
    if isinstance(t, tuple):
        if PyState.has_typing:
            return typing.Tuple[t]
        else: raise ValueError('Cannot implicitly find tuple strategy on python versions <3.5')
    elif isinstance(t, list):
        if PyState.has_typing:
            [t_] = t
            return typing.List[t_]
        else:
            raise ValueError('Cannot implicitly find list strategy on python versions <3.5')

    return t
