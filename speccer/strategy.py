# strategy.py - Strategies for producing arguments to model commands
# author: Ben Simner 

import string
import inspect
import itertools
import functools
import collections
import logging
import abc

__all__ = ['MissingStrategyError', 
            'value_args', 
            'values', 
            'given', 
            'Strategy',
            'has_strat_instance',
            'get_strat_instance',
            'map_strategy',
]

class MissingStrategyError(Exception):
    pass

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
    yield from generate_args_from_generators(*map(functools.partial(values, depth), types))

def generate_args_from_generators(*generators):
    '''Generates a list of n-tuples of `generators' generation instances
    (i.e. permutations of `generators')
    '''
    type_gen = collections.deque(generators)
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


def values(depth, typ, guard=None):
    '''Generate all results for some type 'typ'
    to depth 'depth'

    Checking partials against 'guard' function
    '''
    strat = StratMeta.get_strat_instance(typ)
    yield from strat_values(depth, strat, guard=guard)

def strat_values(depth, strat, guard=None):
    '''Generate all results for some `Strategy` 'strat'
    up to depth 'depth'
    '''
    yield from strat.values(depth, guard=guard)

def given(*ts, **kws):
    '''Decorator to supply generation functions to a function

    Example:

        @given(int)
        def f(x, int_gen_func):
            for i in int_gen_func(depth=3):
                print(x*i)

        f(2)

    will print all even integers to depth 3
    '''
    given_ts = ()
    given_kws = {}

    for t in ts:
        v = functools.partial(generate, t)
        given_ts += (functools.partial(generate, t), )

    for k,t in kws.items():
        given_kws[k] = functools.partial(generate, t)

    def _decorator(f):
        @functools.wraps(f)
        def _wrapper(*args, **kwargs):
            kwargs.update(given_kws)
            return f(*(args + given_ts), **kwargs)
        return _wrapper
    return _decorator

def has_strat_instance(t):
    try:
        StratMeta.get_strat_instance(t)
        return True
    except MissingStrategyError:
        return False

    raise ValueError(t)

def get_strat_instance(t):
    try:
        return StratMeta.get_strat_instance(t)
    except MissingStrategyError:
        return False

    raise ValueError(t)

class StratMeta(abc.ABCMeta):
    '''Metaclass for an strat generator
    handles setting up the LUT
    ''' 
    __strats__ = {} 
    
    def __init__(self, *args, **kwargs):
        pass
    
    def __new__(mcls, name, bases, namespace, _subtype=None, autoregister=True):
        cls = super().__new__(mcls, name, bases, namespace)

        for base in bases:
            try:
                if base._subtype:
                    if autoregister:
                        StratMeta.__strats__[base._subtype] = cls
                        cls._subtype = base._subtype
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
        # lookup in __strats__
        if sub in StratMeta.__strats__:
            return StratMeta.__strats__[sub]

        return self.__class__(self.__name__, (self,) + self.__bases__,
                          dict(self.__dict__),
                          _subtype=sub)

    @staticmethod
    def get_strat_instance(t):
        # see if we have an instance for t, outright
        try:
            return StratMeta.__strats__[t]
        except KeyError:
            # for typing.Generic instances
            # try break up t into its origin and paramters
            # and see if we have a strat instances for those.
            # if we do, compose them together.
            # and put that composition in our StratMeta dict.
            # this allows generation of higher-kinded types such as List[]
            try:
                origin = t.__origin__
                params = t.__parameters__

                strat_origin = StratMeta.get_strat_instance(origin)

                class _GenStrat(Strategy[t]):
                    def generate(self, d, partial=strat_origin.initial(), max_depth=strat_origin.max_depth()):
                        strat_gen = functools.partial(strat_origin.generate, d, partial=partial, max_depth=max_depth)
                        yield from strat_gen(d, *params)
                
                StratMeta.__strats__[t] = _GenStrat
                return _GenStrat
            except AttributeError:
                raise MissingStrategyError('Cannot get Strategy instance for ~{}, not a typing.Generic instance'.format(t))
        raise MissingStrategyError('Cannot get Strategy instance for ~{}'.format(t))

class StrategyIterator:
    log = logging.getLogger('strategy.iterator')

    def __init__(self, strat):
        self.strategy = strat
        self._partials = collections.deque([(strat.initial(), 0)])
        self._values = collections.deque()

    def __next__(self):
        '''Get the next element in the sequence
        '''

        if self._values:
            return self._values.popleft()

        if not self._partials:
            self.log.debug('no more partials')
            raise StopIteration

        max_depth = self.strategy._depth
        guard = self.strategy._guard

        partial, depth = self._partials.popleft()

        if depth <= max_depth:
            trie = self.strategy.generate(depth, partial, max_depth=max_depth)
            for p, l in trie:
                l, l2 = itertools.tee(l)

                if p and guard and not guard(p, *l):
                    self.log.debug('partial `{p}` failed guard'.format(p=p)) 
                    continue

                l2 = list(l2)
                if l2:
                    self._values.extend(l2)

                if p:
                    self.log.debug('got partial `{p}` at depth {d}'.format(p=p, d=depth))
                    self._partials.append((p, depth+1))

        # now check for values
        if self._values:
            return self._values.popleft()

        elif self._partials:
            return self.__next__()

        raise StopIteration

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

    def __init__(self, max_depth, guard=None):
        self._nodes = []
        self._depth = max_depth
        self._guard = guard

    @abc.abstractstaticmethod
    def generate(depth, partial, *, max_depth):
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

    @classmethod
    def max_depth(cls):
        '''Returns the initial 'max_depth' value from this :class:`Strategy`'s
        :meth:`generate` method.
        '''
        s = inspect.signature(cls.generate)
        i = s.parameters['max_depth']
        if i.default is inspect._empty:
            return None
        return i.default

    @classmethod
    def values(cls, depth, *, guard=None):
        '''Returns the list of values this :class:`Strategy` generates
        for some givne depth 'depth'
        '''
        cls_name = cls.__name__
        cls.log.debug('getting values for {cls_name} to depth {depth}'.format(cls_name=cls_name, depth=depth))
        return cls(depth, guard=guard)

    def __iter__(self):
        return StrategyIterator(self)

    def __next__(self):
        raise NotImplementedError

    def __repr__(self):
        name = self.__class__.__name__
        return '{}({})'.format(name, self._depth)

def map_strategy(strat_instance_type, super_strat, **kwargs):
    '''Create a new strategy for 'strat_instance_type' by decorating a generator function
    that yields new values from partials generated from 'super_strat'

    i.e.
    class Nat:
        S = lambda n: Nat(n)
        Z = Nat()
        def __init__(self, suc=None):
            self.suc = suc

    @map_strategy(Nat, Strategy[int])
    def IntStrat(nat):
        def nat_to_int(n):
            if n.suc is None:
                return 0
            return 1 + nat_to_int(n.suc)
        yield nat_to_int(nat)
        yield - nat_to_int(nat)
    '''
    def decorator(f):
        ss = super_strat(None) # do not iterate over

        class MapStrat(Strategy[strat_instance_type], **kwargs):
            def generate(self, depth, partial=super_strat.initial(), max_depth=None):
                for k, vs in ss.generate(depth, partial=partial, max_depth=max_depth):
                    for v in vs:
                        yield k, f(depth, v, max_depth=max_depth)
        return MapStrat
    return decorator
