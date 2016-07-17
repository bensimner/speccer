from builtins import tuple as _tuple
import os
import abc
import enum
import inspect

class PropertyType(enum.Enum):
    FORALL = 1
    EXISTS = 2
    UNIT = 3
    EMPTY = 4

    OR = 5
    AND = 6


class Outcome(abc.ABC):
    def __init__(self, prop, assertions):
        self.prop = prop
        self._asserts = assertions
        self._extra_args = []

        # execution state
        # for nice output
        self.state = {
            'calls': 0,
            'depth': 0,
            'failed_implications': 0,
        }

    @property
    def assertions(self):
        '''The list of assertion messages that *passed* during the execution
        to find this Outcome
        '''
        return self._asserts

    @abc.abstractproperty
    def reason(self):
        '''Reason for Outcome

        Could be witness or counterexample objects if one exists
        or None
        '''

    def __repr__(self):
        if self._extra_args != []:
            _extra = ', '.join(list(map(repr, self._extra_args)))
            return '<%s(%s, %s, %s)>' % (self.__class__.__name__, self.prop, self.reason, _extra)

        return '<%s(%s, %s)>' % (self.__class__.__name__, self.prop, self.reason)

class Success(Outcome):
    @property
    def reason(self):
        return 'N/A'

class UnitSuccess(Success):
    def __init__(self, clause):
        super().__init__(clause, [])

    @property
    def reason(self):
        return '<unit>'

class Witness(Success):
    def __init__(self, prop, witness, assertions=None):
        super().__init__(prop, assertions)
        self._witness = witness

    @property
    def reason(self):
        return self._witness

class Failure(Outcome):
    def __init__(self, prop, assertions=None, message='Unspecified Failure'):
        self._msg = message
        super().__init__(prop, assertions)

    @property
    def reason(self):
        return self._msg

class EmptyFailure(Failure):
    def __init__(self, clause):
        super().__init__(clause, [])

    @property
    def reason(self):
        return '<empty>'


class NoWitness(Failure):
    pass

class UnrelatedException(Failure):
    def __init__(self, prop, exception, assertions=None):
        super().__init__(prop, assertions)
        self._e = exception

    @property
    def reason(self):
        return self._e

class Counter(Failure):
    def __init__(self, prop, counter, assertions=None):
        super().__init__(prop, assertions)
        self._counter = counter

    @property
    def reason(self):
        return self._counter

class AssertionCounter(Counter):
    def __init__(self, prop, counter, msg, assertions=None):
        super().__init__(prop, counter, assertions=assertions)
        self._msg = msg
        self._extra_args.append(msg)

    @property
    def message(self):
        return self._msg

class NoCounter(Success):
    pass

def _get_name(i=0, depth=5):
    '''Inspect Stack to get a relative name for this code point
    '''
    stk = inspect.stack()[(2 + i):depth]
    loc = []
    _last_fn = None
    for sf in reversed(stk):
        fn, _ = os.path.splitext(sf.filename)
        _, fn = os.path.split(fn)
        f = sf.function
        if _last_fn != fn:
            loc.append('{}.{}'.format(fn, f))
        else:
            loc.append(f)
        _last_fn = fn
    return ':'.join(loc)

class Property(tuple):
    def __new__(cls, type, args, name=None):
        return _tuple.__new__(cls, (type, args))

    def __init__(self, type, args, name=None):
        self.name = name or _get_name(i=1)
        self.type = type
        self.args = args
        # each Property clause can have a parent clause
        # for nested properties
        self.parent = None

        # the Property can store its current, partially evaluated state
        # (assertions_log, counterexample/witness)
        self.partial = (None, None)

    def __and__(self, other):
        if not isinstance(other, Property):
            raise TypeError('Can only & together Property instances')

        return Property(PropertyType.AND, [self, other])

    def __add__(self, other):
        if not isinstance(other, Property):
            raise TypeError('Can only + together Property instances')

        return Property(PropertyType.OR, [self, other])

    def __mul__(self, other):
        if not isinstance(other, Property):
            raise TypeError('Can only * together Property instances')

        return Property(PropertyType.AND, [self, other])

    def __or__(self, other):
        if not isinstance(other, Property):
            raise TypeError('Can only | together Property instances')

        return Property(PropertyType.OR, [self, other])

    @property
    def failed_implications(self):
        if self.type not in [PropertyType.FORALL, PropertyType.EXISTS]:
            return 0

        types, _ = self.args
        c = 0
        for t in types:
            if getattr(t, '_failed_implications', False):
                c += t._failed_implications
        return c

    def reset_implications(self):
        if self.type not in [PropertyType.FORALL, PropertyType.EXISTS]:
            return

        types, _ = self.args
        for t in types:
            if getattr(t, '_failed_implications', False):
                t._failed_implications = 0

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

def empty():
    '''The empty property

    Always fails
    '''
    return Property(PropertyType.EMPTY, [])

def unit():
    '''The unit property

    Always passes
    '''
    return Property(PropertyType.UNIT, [])

def forall(*args):
    '''Forall `type` the function 'f' holds
    where f either returns `bool` or another `Property`
    '''
    *types, f = args
    return Property(PropertyType.FORALL, [types, f], name=_get_name(i=0))

def exists(*args):
    '''There exists some `type` such that the function 'f' holds
    where f either returns `bool` or another `Property`
    '''
    *types, f = args
    return Property(PropertyType.EXISTS, [types, f], name=_get_name(i=0))
