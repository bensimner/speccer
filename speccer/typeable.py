import attr
import typing

@attr.s
class Typeable:
    typ = attr.ib()
    origin = attr.ib()
    args = attr.ib()
    arity = attr.ib()

    def pretty(self):
        if not self.origin:
            name = self.typ.__name__
        else:
            name = self.origin.pretty()

        if self.args:
            args = [from_type(a).pretty() for a in self.args]
            return '{}[{}]'.format(name, ', '.join(args))

        return '{}'.format(name)

def from_type(t):
    '''Converts a type `t` to a Typeable
    '''
    if isinstance(t, Typeable):
        return t

    if isinstance(t, list):
        if len(t) != 1:
            if len(t) < 1:
                reason = 'Missing type parameter'
            else:
                reason = 'Too many type parameters, only homogenous lists allowed'
            msg = 'Can only use literal list alias with a single type, `{}` is invalid: {}'
            raise ValueError(msg.format(repr(t), reason))
        t0 = from_type(t[0]).typ
        return from_type(typing.List[t0])
    elif isinstance(t, set):
        if len(t) != 1:
            if len(t) < 1:
                reason = 'Missing type parameter'
            else:
                reason = 'Too many type parameters, only homogenous sets allowed'
            msg = 'Can only use literal set alias with a single type, `{}` is invalid: {}'
            raise ValueError(msg.format(repr(t), reason))
        t0 = from_type(next(iter(t))).typ
        return from_type(typing.Set[t0])
    elif isinstance(t, tuple):
        args = tuple([from_type(a).typ for a in t])
        return from_type(typing.Tuple[args])

    return _from_typing36(t)

def _from_typing36(t):
    '''Support for 3.6 version of typing module
    '''

    try:
        origin = t.__origin__
    except AttributeError:
        # not typing.Generic
        return Typeable(typ=t, origin=None, args=[], arity=0)

    # is a base type
    if not origin:
        return Typeable(typ=t, origin=None, args=[], arity=1)

    args = [from_type(t_) for t_ in t.__args__]
    return Typeable(typ=t, origin=from_type(origin), args=args, arity=get_arity(origin, args))

def get_arity(origin, args=[]):
    '''Gets the arity of some typing type
    '''
    if isinstance(origin, typing.Generic):
        return 1 - (1 if args else 0)

    return 0
