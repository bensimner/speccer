# strategy.py - Strategies for producing arguments to model commands
# author: Ben Simner 

import string
import sys
import inspect
import itertools
import functools
import collections
import contextlib
import logging
import abc

sys.setrecursionlimit(40)

__all__ = ['MissingStrategyError', 
            'value_args', 
            'values',
            'Strategy',
            'register',
            'has_strat_instance',
            'mapS',
            'change_strategies',
            'implication',
            'ImplicationException',
]

class MissingStrategyError(Exception):
    pass

class ImplicationException(Exception):
    pass

def implication(implication_function):
    sig = inspect.signature(implication_function)
    
    # enforce unary functions
    if len(sig.parameters) != 1:
        raise ValueError('`implication` expected function of 1 parameter')

    for param in sig.parameters.values():
        pass

    if param.annotation is sig.empty:
        raise ValueError('`implication` expected non-empty annotation for parameter `{}`'.format(param.name))

    def decorator(p):
        @mapS(Strategy[param.annotation], autoregister=True)
        def newStrat(d, v, *args):
            if not implication_function(v):
                raise ImplicationException

            yield v

        
        p.strategies[param.annotation] = newStrat
        return p

    return decorator

def values(depth, t):
    yield from Strategy[t](depth)

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
    yield from generate_args_from_strategies(*map(functools.partial(values, depth), types))

def generate_args_from_strategies(*strategies):
    '''Generates a list of n-tuples of `generators' generation instances
    (i.e. permutations of `generators')
    '''
    type_gen = collections.deque(strategies)
    poss = collections.deque()
    poss.append([])
    new_poss = collections.deque()
    
    while type_gen:
        gen = type_gen.popleft()

        try:
            for v in gen:
                for ks in poss:
                    new_poss.append(ks + [v])
        except MissingStrategyError:
            for ks in poss:
                new_poss.append(ks + [MissingStrategyError])

        poss = new_poss
        new_poss = collections.deque()

    yield from map(tuple, poss)

def has_strat_instance(t):
    try:
        StratMeta.get_strat_instance(t)
        return True
    except MissingStrategyError:
        return False

    raise ValueError(t)

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

                class _GenStrat(self.new(t)):
                    def generate(self, d, *args, partial=strat_origin.initial()):
                        strat_instance = strat_origin(d)
                        yield from strat_instance.generate(d, *(params + args), partial=partial)
                
                StratMeta._current_strategies[t] = _GenStrat
                return _GenStrat
            except AttributeError:
                raise MissingStrategyError('Cannot get Strategy instance for ~{}, not a typing.Generic instance'.format(t))
        raise MissingStrategyError('Cannot get Strategy instance for ~{}'.format(t))

class StrategyIterator:
    def __init__(self, strat):
        name = str(strat)
        self.log = logging.getLogger('strategy.iterator({})'.format(name))

        self.strategy = strat
        self._partials = collections.deque([(strat.initial(), 0)])
        self._values = collections.deque()
        self._next_generator = self.next_generator()

    def next_generator(self):
        max_depth = self.strategy._depth

        while True:
            if not self._partials:
                break

            partial, depth = self._partials.popleft()

            if depth <= max_depth:
                # TODO: Try remove recursion here
                # maybe by doing some memoization
                trie = iter(self.strategy.generate(depth, partial=partial))
                while True:
                    try:
                        p, l = next(trie)
                        l, l2 = itertools.tee(l)
                        l2 = list(l2)
                    except ImplicationException:
                        continue
                    except StopIteration:
                        break
                    else:
                        self.log.debug('for partial `{p}`'.format(p=p)) 

                        if l2:
                            yield from l2

                        if p is not None: 
                            self.log.debug('got partial `{p}` at depth {d}'.format(p=p, d=depth))
                            self._partials.append((p, depth+1))
                            self.log.debug('partials = {}'.format(self._partials))

    def __next__(self):
        '''Get the next element in the sequence
        '''
        self.log.debug('next')
        return next(self._next_generator)

    def __iter__(self):
        return self
    
    def __repr__(self):
        return 'StrategyInstance({})'.format(repr(self.strategy))

    def copy(self):
        '''Returns a copy of this Strategy instance at its current 
        position
        '''
        si = StrategyInstance(self.strategy)
        si._partials = self._partials.copy()
        si._values = self._values.copy()
        return si

class Strategy(metaclass=StratMeta): 
    '''A :class:`Strategy` is a method of generating values of some type
    in a deterministic, gradual way - building smaller values first

    In future: this will be a wrapper around a generator (defined by `Strategy.generate')
    '''

    log = logging.getLogger('strategy')

    def __init__(self, max_depth):
        self._nodes = []
        self._depth = max_depth

    def values(self, depth, *args, partial):
        for _, v in self.generate(depth, *args, partial=partial):
            yield from v

    def cons(self, strat):
        '''Is essentially the same as ``yield from strat(self._depth - 1)``
        '''
        yield from strat(self._depth - 1)

    @abc.abstractmethod
    def generate(self, depth, *args, partial):
        '''Generator for all values of depth 'depth'
        Starting with initial 'partial' value
        
        Returns a generator of pairs x, y
        where 
            x = child node
            y = list of partial results

        generate(partial=x, depth=depth) can then be yielded from
        to recrusively generate the trie (see :meth:`values`)

        Finally, a `max_depth' parameter is passed to indicate the 
        maximum depth 
        '''

    @classmethod
    def initial(cls):
        '''Returns the initial 'partial' value from this :class:`Strategy`'s
        :meth:`generate` method.
        '''
        s = inspect.signature(cls.generate)
        i = s.parameters['partial']
        if i.default is inspect._empty:
            return None
        return i.default

    def __iter__(self):
        return StrategyIterator(self)

    def __next__(self):
        raise NotImplementedError

    def __repr__(self):
        name = self.__class__.__name__
        return '{}({})'.format(name, self._depth)

def mapS(strat, register_type=None, autoregister=False, **kwargs):
    '''
    Maps some function over a strategies values.
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
        class MapStrat(strat, **kwargs):
            def generate(self, depth, *args, partial=strat.initial()):
                for k, vs in strat.generate(super(), depth, *args, partial=partial):
                    def _generator():
                        for v in vs:
                            yield from f(depth, v, *args)

                    yield k, _generator()

        if register_type:
            register(register_type, MapStrat)

        MapStrat.__name__ = 'Mapped_{}'.format(strat.__name__)
        return MapStrat
    return decorator
