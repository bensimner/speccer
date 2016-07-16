import contextlib
import collections

def intersperse(*its):
    iters = collections.deque(map(iter, its))
    while iters:
        with contextlib.suppress(StopIteration):
            i = iters.popleft()
            yield next(i)
            iters.append(i)


def pretty_type(t):
    '''Pretty string of some type
    '''
    try:
        # typing.GenericMeta
        return '{}[{}]'.format(t.__name__, ', '.join(map(pretty_type, t.__parameters__)))
    except AttributeError:
        try:
            # typing.TupleMeta
            if t.__tuple_use_ellipsis__:
                return '{}[{}, ...]'.format(t.__name__, ', '.join(map(pretty_type, t.__tuple_parameters__)))
            else:
                return '{}[{}]'.format(t.__name__, ', '.join(map(pretty_type, t.__tuple_parameters__)))
        except AttributeError:
            try:
                return t.__name__
            except AttributeError:
                return str(t)
