# strategy.py - Strategies for producing arguments to model commands
# author: Ben Simner 

import string
import inspect
import itertools
import functools
import abc

class MissingStrategyError(Exception):
    pass

def generate(typ, depth, partial=None):
    '''Generate some strategy of some depth
    '''
    strat = StratMeta.get_strat_instance(typ)
    if partial:
        yield from strat.generate(depth, partial=partial, max_depth=depth)
    else:
        yield from strat.generate(depth, max_depth=depth)

def values(typ, depth, guard=None):
    '''Generate all results for some type 'typ'
    to depth 'depth'

    Checking partials against 'guard' function
    '''
    strat = StratMeta.get_strat_instance(typ)
    yield from strategy_generate(strat, depth, guard=guard)

def strategy_generate(strat, depth, guard=None):
    '''Generate all results for some :class:`Strategy` 'strat'
    up until some depth 'depth', checking all partials against some 
    guard condition 'guard'
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
                strat_params = list(map(StratMeta.get_strat_instance, params))

                class _GenStrat(Strategy[t]):
                    def generate(d, max_depth, partial=None):
                        strat_gen = functools.partial(strat_origin.generate, d, max_depth, partial=partial)
                        return strat_gen(*params)
                
                StratMeta.__strats__[t] = _GenStrat
                return _GenStrat
            except AttributeError:
                raise MissingStrategyError('Cannot get Strategy instance for ~{}, not a typing.Generic instance'.format(t))
        raise MissingStrategyError('Cannot get Strategy instance for ~{}'.format(t))

class Strategy(metaclass=StratMeta): 
    '''A :class:`Strategy` is a method of generating values of some type
    in a deterministic, gradual way - building smaller values first
    '''
    @abc.abstractstaticmethod
    def generate(depth, partial, max_depth):
        '''Generator for all values of depth 'depth'
        Starting with initial 'partial' value
        
        Returns a generator of pairs x, y
        where 
            x = child node
            y = list of partial results

        generate(partial=x, depth=depth) can then be yielded from
        to recrusively generate the trie (see :meth:`values`)
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
        '''Returns the initial 'partial' value from this :class:`Strategy`'s
        :meth:`generate` method.
        '''
        s = inspect.signature(cls.generate)
        i = s.parameters['max_depth']
        if i.default is inspect._empty:
            return None
        return i.default

    @classmethod
    def values(cls, depth, guard=None):
        '''Returns the list of values this :class:`Strategy` generates
        for some givne depth 'depth'
        '''
        yield from cls._trie_to_list(cls.generate(depth=0, max_depth=depth), 0, depth, guard=guard)

    @classmethod
    def _trie_to_list(cls, trie, depth, max_depth, guard=None):
        '''TODO:
            Make this do IDS or breadth-first search
        '''

        nodes = [(trie, depth)]

        while len(nodes) > 0:
            (trie, depth), *nodes = nodes

            if depth < max_depth:
                for p, l in trie:
                    # yield the partial result
                    if p and guard and not guard(p):
                        continue

                    for v in l:
                        yield v

                    if p:
                        t = cls.generate(depth + 1, partial=p, max_depth=max_depth)
                        nodes.append((t, depth + 1))

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
        class MapStrat(Strategy[strat_instance_type], **kwargs):
            def generate(depth, max_depth=None, partial=super_strat.initial()):
                for k, vs in super_strat.generate(depth, partial=partial, max_depth=max_depth):
                    for v in vs:
                        yield k, f(depth, v, max_depth=max_depth)
        return MapStrat
    return decorator
