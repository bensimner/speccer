# strategy.py - Strategies for producing arguments to model commands
# author: Ben Simner 

import abc
import sys
import math
import heapq
import string
import typing
import logging
import inspect
import itertools
import functools
import contextlib
import collections

from .error_types import *

FAILED_IMPLICATION = 0
log = logging.getLogger('strategy')

__all__ = [
            'value_args', 
            'values',
            'Strategy',
            'register',
            'has_strat_instance',
            'get_strat_instance',
            'mapS',
            'change_strategies',
            'implication',
]

def implication(implication_function):
    impl_name = implication_function.__name__
    sig = inspect.signature(implication_function)
    param = next(iter(sig.parameters.values()))

    t = param.annotation
    if t is sig.empty:
        # maybe try type inference?
        raise ValueError('implication: `{}` missing type-annotation for parameter: `{}`'.format(impl_name, param.name)) 

    def decorator(p_func):
        @mapS(Strategy[t])
        def newStrat(d, v, *args):
            global FAILED_IMPLICATION
            try:
                if implication_function(v) == False:
                    FAILED_IMPLICATION += 1
                    raise StopIteration
            except AssertionFailure as e:
                e._info['value'] = v
                raise
            else:
                yield v

        newStrat.__name__ = implication_function.__name__ 

        @functools.wraps(p_func)
        def p(*args, **kwargs):
            prop = p_func(*args, **kwargs)
            prop.strategies[t] = newStrat
            return prop
        return p

    return decorator

def values(depth, t):
    yield from Strategy.get_strat_instance(t)(depth)

@contextlib.contextmanager
def change_strategies(strategies):
    c_strats = StratMeta._current_strategies.copy()
    c_strats.update(strategies)
    
    set_strategies(c_strats)
    yield
    reset_strategies()


def set_strategies(strategies):
    '''Set the current LUT of strategies to something
    '''
    StratMeta._current_strategies = strategies

def reset_strategies():
    '''Reset the current LUT of strategies back to default
    '''
    StratMeta._current_strategies = StratMeta.__strats__

def value_args(depth, *types): 
    '''Creates a `Strategy' which generates all tuples of type *types
    i.e. 
        value_args(1, str, int) ->
            ('a', 0)
            ('a', 1)
            ('a', -1)
            ('b', 0)
            ('b', 1)
            ('b', -1)
            ...
            ('bb' 0)
            ('bb' 1)
            ('bb' -1)

    If any given type has no strategy instance then a MissingStrategyError is put there instead
    i.e.
        value_args(1, int, MyTypeWithNoStratInstance) ->
            (0, MissingStrategyError)
            (1, MissingStrategyError)
            (-1, MissingStrategyError)
    ''' 
    yield from generate_args_from_strategies(*map(lambda t: values(depth, t), types))

class PairGen:
    @functools.total_ordering
    class _Pair:
        def __init__(self, *x):
            self.x = x

        def __repr__(self):
            return 'Pair{x}'.format(self.x)

        def __eq__(self, o):
            return all(map(lambda x, y: x == y, self.x, o.x))

        def __lt__(self, o):
            return all(map(lambda x, y: x < y, self.x, o.x))
            
    # A priority queue
    # (x, y) < (a, b) => x < a AND y < b
    def __init__(self, n=2):
        pair = PairGen._Pair(*tuple(0 for _ in range(n)))
        self._n = n
        self._memo = {}
        self._pq = []

        # max_sizes, only generate up to this.
        self.max_sizes = [-1 for _ in range(n)]
        self.continuation = {}

        heapq.heappush(self._pq, pair)

    def update(self, i):
        '''Increment max_sizes for index i
        '''
        self.max_sizes[i] += 1
        if i in self.continuation:
            t = self.continuation[i]
            pair = PairGen._Pair(*t)
            heapq.heappush(self._pq, pair)
            del self.continuation[i]

    def __iter__(self):
        return self

    def __next__(self):
        if not self._pq:
            raise StopIteration

        pair = heapq.heappop(self._pq)
        t = pair.x

        for i in range(self._n):
            v = t[i] + 1
            tp = t[:i] + (v,) + t[i+1:]

            if v > self.max_sizes[i]:
                if i not in self.continuation:
                    self.continuation[i] = tp
                continue

            if tp not in self._memo:
                pair = PairGen._Pair(*tp)
                heapq.heappush(self._pq, pair)
                self._memo[tp] = True

        return t

def generate_args_from_strategies(*iters):
    '''TODO: change this to do better ordering?
Make sure it hits all lower values first
i.e. 00 01 10 11 before 20 or 02 (1s before 2s)
    '''
    gens = collections.deque(map(iter,iters))
    n = len(gens)

    values = [[] for _ in range(n)]
    ds = collections.deque(enumerate(values))

    pair_gen = PairGen(n=n)
    pair_next = None
    c = 0

    def _check():
        nonlocal pair_next, pair_gen
        while True:
            if not pair_next:
                pair_next = next(pair_gen)

            log.debug('generate_args_from_strategies: \n values = {}\n t = {}'.format(values,pair_next))

            t = ()
            for i in range(n):
                j = pair_next[i]
                t += (values[i][j],)
            else:
                pair_next = None
                yield t
                continue
            break

    while gens:
        gen = gens.popleft()
        di, d = ds.popleft()

        try:
            v = next(gen)
        except StopIteration:
            continue
        except MissingStrategyError:
            v = MissingStrategyError
            ds.append((di,d))
        else:
            ds.append((di,d))

        pair_gen.update(di)
        d.append(v)
        c += 1
        gens.append(gen)
        if c >= n:
            yield from _check()

    if c >= n:
        yield from _check()

def has_strat_instance(t):
    try:
        Strategy.get_strat_instance(t)
        return True
    except MissingStrategyError:
        return False

    raise ValueError(t)

def get_strat_instance(t):
    '''Gets the strategy instance registered to some type 't'
    '''
    return Strategy.get_strat_instance(t)

def register(t, strategy, override=True):
    '''Register a :class:`Strategy` instance for 
    type 't'
    '''
    if t in StratMeta.__strats__ and not override:
        raise ValueError

    StratMeta.__strats__[t] = strategy

class StratMeta(abc.ABCMeta):
    '''Metaclass for an strat generator
    handles setting up the LUT
    ''' 
    # global LUT of all strategies
    __strats__ = {} 

    # LUT for this current search
    _current_strategies = __strats__
    
    def __init__(self, *args, **kwargs):
        pass
    
    def __new__(mcls, name, bases, namespace, _subtype=None, autoregister=True):
        cls = super().__new__(mcls, name, bases, namespace)

        for base in bases:
            try:
                if base._subtype:
                    cls._subtype = base._subtype

                    if autoregister:
                        register(base._subtype, cls)
            except AttributeError:
                pass

        if _subtype:
            cls._subtype = _subtype

        cls.__autoregister__ = autoregister
        return cls

    def __getitem__(self, args):
        if not isinstance(args, tuple):
            args = (args,)

        sub, = args

        try:
            return self.get_strat_instance(sub)
        except MissingStrategyError:
            pass

        return self.new(sub)

    def new(self, t):
        return self.__class__(self.__name__, (self,) + self.__bases__,
                          dict(self.__dict__),
                          _subtype=t)

    def get_strat_instance(self, t):
        # see if we have an instance for t, outright
        try:
            return StratMeta._current_strategies[t]
        except KeyError:
            # for typing.Generic instances
            # try break up t into its origin and paramters
            # and see if we have a strat instances for those.
            # if we do, compose them together.
            # and put that composition in our StratMeta dict.
            # this allows generation of higher-kinded types such as List[~T]
            try:
                origin = t.__origin__
                params = t.__parameters__

                strat_origin = self.get_strat_instance(origin)

                s = self.new(t)
                def generate(self, d, *args):
                    strat_instance = strat_origin(d)
                    yield from strat_instance.generate(d, *(params + args))

                name = 'Generated_{}[{}]'.format(strat_origin.__name__, tuple(map(lambda p: p.__name__, params)))
                GenStrat = type(name, (s,), dict(generate=generate))
                GenStrat.__module__ = strat_origin.__module__
                StratMeta._current_strategies[s] = GenStrat
                return GenStrat
            except AttributeError:
                try:
                    tuple_params = t.__tuple_params__
                    if tuple_params is None:
                        raise MissingStrategyError
                    tuple_use_ellipsis = t.__tuple_use_ellipsis__
                    strat_origin = self.get_strat_instance(typing.Tuple)
                    s = self.new(t)
                    def generate(self, d, *args):
                        strat_instance = strat_origin(d)
                        yield from strat_instance.generate(d, *(tuple_params + args))

                    name = 'GeneratedTuple_[{}]'.format(tuple(map(lambda p: p.__name__, tuple_params)))
                    GenStrat = type(name, (s,), dict(generate=generate))
                    GenStrat.__module__ = strat_origin.__module__
                    StratMeta._current_strategies[s] = GenStrat
                    return GenStrat
                except AttributeError:
                    raise MissingStrategyError('Cannot get Strategy instance for ~{}, not a typing.Generic instance'.format(t))
        raise MissingStrategyError('Cannot get Strategy instance for ~{}'.format(t))

class StrategyIterator:
    def __init__(self, strat):
        self.strategy = strat
        self._generator = strat.generate(strat._depth)

        name = str(strat)
        self.log = logging.getLogger('strategy.iterator({})'.format(name))

    def __next__(self):
        if self.strategy._depth > 0:
            return next(self._generator)
         
        raise StopIteration

    def __iter__(self):
        return self
    
    def __repr__(self):
        return 'StrategyInstance({})'.format(repr(self.strategy))

class Strategy(metaclass=StratMeta): 
    '''A :class:`Strategy` is a method of generating values of some type
    in a deterministic, gradual way - building smaller values first

    In future: this will be a wrapper around a generator (defined by `Strategy.generate')
    '''
    log = logging.getLogger('strategy')

    def __init__(self, max_depth):
        self.log.debug('new({})'.format(max_depth))
        self._nodes = []
        self._depth = max_depth

    def cons(self, f):
        '''Basically, takes some function `f`
        looks at its type signature
        and then creates (and yields from) a strategy to generate inputs to that function

        i..e
        '''
        sig = inspect.signature(f)
        types = list(map(lambda p: p[1].annotation, sig.parameters.items()))

        self.log.debug('cons{}, d={}'.format(tuple(types), self._depth))
        for argt in value_args(self._depth - 1, *types):
            self.log.debug('cons: {}'.format(argt))
            yield f(*argt)

    @abc.abstractmethod
    def generate(self, depth, *args):
        '''Generator for all values of depth 'depth'

        Allows extra args for higher-kinded types
        '''

    def __iter__(self):
        return StrategyIterator(self)

    def __next__(self):
        raise NotImplementedError

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        name = self.__class__.__name__
        return '{}({})'.format(name, self._depth)

def mapS(strat, register_type=None, autoregister=False, **kwargs):
    '''
    Maps some function over a Strategy _class_.
    To automatically register the new strategy either set 
        autoregister=True   overwrite the old strategy with this one
        register_type=t     register this strategy for type 't'

    i.e.
    @mapS(Strategy[int])
    def NewIntStrat(depth, value):
        yield 'new({})'.format(value)

    NewIntStrat(3) ~= ['new(0)', 'new(1)', 'new(-1)', 'new(2)', 'new(-2)', 'new(3)', 'new(-3)']
    '''
    def decorator(f):
        class MapStrat(strat, autoregister=autoregister, **kwargs):
            def generate(self, depth, *args):
                for v in strat.generate(self, depth, *args):
                    yield from f(depth, v, *args)

        name = 'Mapped[{}]_{}'.format(f.__name__, strat.__name__)

        if register_type:
            register(register_type, MapStrat)

        MapStrat.__name__ = f.__name__
        MapStrat.__module__ = strat.__module__
        return MapStrat
    return decorator
