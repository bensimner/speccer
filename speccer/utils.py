import collections

from . import PyState
if PyState.has_typing:
    import typing

def intersperse(*its):
    iters = collections.deque(map(iter, its))
    rets = collections.deque([None for _ in range(len(its))])
    while iters:
        try:
            i = iters.popleft()
            ret = rets.popleft()
            yield next(i)
            rets.append(ret)
            iters.append(i)
        except StopIteration as e:
            rets.append(e.value)

    return tuple(rets)


def pretty_type(t):
    '''Pretty string of some type
    '''
    try:
        return '{}[{}]'.format(t.__name__, ', '.join(map(pretty_type, t.__args__)))
    except:
        pass

    try:
        # typing.GenericMeta
        return '{}[{}]'.format(t.__name__, ', '.join(map(pretty_type, t.__parameters__)))
    except AttributeError:
        try:
            # typing.TupleMeta
            if t.__tuple_use_ellipsis__:
                return '{}[{}, ...]'.format(t.__name__, ', '.join(map(pretty_type, t.__tuple_params__)))
            else:
                return '{}[{}]'.format(t.__name__, ', '.join(map(pretty_type, t.__tuple_params__)))
        except AttributeError:
            try:
                return t.__name__
            except AttributeError:
                return str(t)

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
