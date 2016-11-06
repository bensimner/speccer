import os
import abc
import types
import inspect
import contextlib

from . import utils
from . import strategy
from . import clauses
from . import asserts

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

def _get_name_from_func(func, other):
    if not isinstance(func, types.LambdaType):
        with contextlib.suppress(AttributeError):
            return func.__qualname__

        with contextlib.suppress(AttributeError):
            return func.__name__

    return other

def _get_path(i=0, depth=None):
    '''Inspect Stack to get a relative name for this code point
    '''
    stk = inspect.stack()[(2 + i):depth]
    loc = []

    for sf in reversed(stk):
        _, fn = os.path.split(sf.filename)
        f = sf.function
        loc.append('[{}]{}'.format(fn, f))

    return ':'.join(loc)

class Property:
    '''A Property is the core concept in speccer

    It represents a piece of computation that can be evaluated to a success or a failure
    '''
    def __init__(self, name=None):
        self.path = _get_path(i=1)
        self.name = name or type.name

        # each Property clause can have a parent clause
        # for nested properties
        self.parent = None

        # the Property can store its current, partially evaluated state
        # (assertions_log, counterexample/witness)
        self.partial = (None, None)

    def __and__(self, other):
        if not isinstance(other, Property):
            raise TypeError('Can only & together Property instances')

        return _and(self, other)

    def __add__(self, other):
        if not isinstance(other, Property):
            raise TypeError('Can only + together Property instances')

        return _or(self, other)

    def __mul__(self, other):
        if not isinstance(other, Property):
            raise TypeError('Can only * together Property instances')

        return _and(self, other)

    def __or__(self, other):
        if not isinstance(other, Property):
            raise TypeError('Can only | together Property instances')

        return _or(self, other)

    def run(self):
        '''Run a Property until completion
        yield at each step
        and then return the Result
        '''
        raise NotImplementedError

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class Quantified(Property):
    '''A Property that is a function quantified over some type
    '''
    def __init__(self, type, func, name=None, quant_name=None):
        self.type = utils.convert_type(type)
        self.func = func
        if quant_name and not name:
            name = '{}[{}]'.format(_get_name_from_func(func, 'forall'), utils.pretty_type(self.type))
        super().__init__(name=name)

    @property
    def failed_implications(self):
        c = 0
        if getattr(self.type, '_failed_implications', False):
            c += self.type._failed_implications
        return c

    def reset_implications(self):
        if getattr(self.type, '_failed_implications', False):
            self.type._failed_implications = 0


class empty(Property):
    '''The empty property

    >>> prop = empty()
    >>> spec(3, prop)    # empty failure
    '''
    def __init__(self):
        super().__init__(None, name='empty')

    def reset_implications(self):
        pass

    def run(self, _):
        yield
        return EmptyFailure(self)

class unit(Property):
    '''The identity (unit) property

    >>> prop = unit()
    >>> spec(3, prop)    # unit success
    '''
    def __init__(self):
        super().__init__(None, name='unit')

    def reset_implications(self):
        pass

    def run(self, _):
        yield
        return UnitSuccess(self)

def _run_prop_func(depth, prop, type, f):
    '''Runs a property's function with argument of type `type`

    If the property holds,   returns Witness(prop, WITNESS)
    If it does not hold,     returns Counter(prop, COUNTER)
    If an assertion happens, returns AssertionCounter(prop, COUNTER, EXCEPTION)
    '''
    sig = inspect.signature(f)

    for v in strategy.Strategy[type](depth):
        counter = sig.bind(v)

        log = []
        prop.partial = (log, counter)

        try:
            with asserts.change_assertions_log(log):
                v = f(*counter.args, **counter.kwargs)

            if not v:
                yield Counter(prop, counter, assertions=log)
            elif isinstance(v, clauses.Property):
                c = v.run(depth)
                try:
                    while True:
                        next(c)
                except StopIteration as e:
                    yield e.value
            else:
                yield Witness(prop, counter, assertions=log)
        except AssertionError as e:
            yield AssertionCounter(prop, counter, e.args[0], assertions=log)

class forall(Quantified):
    '''Universal quantification

    Takes a type `type` and a function `func`, returning a Property which tests
    `func` against values of type `type` up to some depth.

    >>> prop = forall(int, p)  # for all int's n, p(n) passes
    >>> prop.run(3)            # try prove for all n to depth 3
    '''
    def __init__(self, type, func, name=None):
        super().__init__(type, func, name, quant_name='forall')

    def run(self, depth):
        # run_prop_func just runs the property's func, which is exactly all forall clauses does
        # so there's no required extra step here.
        for v in _run_prop_func(depth, self, self.type, self.func):
            if isinstance(v, Failure):
                return v
            yield

        return NoCounter(self, assertions=v.assertions)

class exists(Quantified):
    '''Existential quantification

    Takes a type `type` and a function `func`, returning a Property which tests
    `func` against values of type `type` up to some depth.

    >>> prop = exists(int, p)  # there exists some int n such that p(n) passes
    >>> prop.run(3)            # try find n to depth 3
    '''
    def __init__(self, type, func, name=None):
        super().__init__(type, func, name, quant_name='exists')

    def run(self, depth):
        # run_prop_func just runs the property's func, which is exactly all an exists clause does
        # so there's no required extra step here.
        for v in _run_prop_func(depth, self, self.type, self.func):
            if isinstance(v, Success):
                return v
            yield

        return NoWitness(self, assertions=v.assertions)


class _or(Property):
    '''p | q, interspereses calls to run(...) on p and q
    returning any Success in p or q
    if no success, then returns the last outcome that was ran
    '''
    def __init__(self, a, b):
        self.lhs = a
        self.rhs = b

    def run(self, depth):
        g = utils.intersperse(self.lhs.run(depth), self.rhs.run(depth))
        while True:
            try:
                yield next(g)
            except StopIteration as e:
                for v in e.value:
                    if isinstance(v, Success):
                        return v
                return v

class _and(Property):
    '''p & q, interspereses calls to run(...) on p and q
    returning any Failure in p or q
    if no failure, then returns the last outcome that was ran
    '''
    def __init__(self, a, b):
        self.lhs = a
        self.rhs = b

    def run(self, depth):
        g = utils.intersperse(self.lhs.run(depth), self.rhs.run(depth))
        while True:
            try:
                yield next(g)
            except StopIteration as e:
                for v in e.value:
                    if isinstance(v, Failure):
                        return v
                return v
