# strategy.py - Strategies for producing arguments to model commands
# author: Ben Simner 

import string
import itertools
import functools
import abc

def generate(typ, depth, guard=None):
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
        cls._subtype = _subtype

        if autoregister:
            for base in bases:
                try:
                    if base._subtype:
                        StratMeta.__strats__[base._subtype] = cls
                except AttributeError:
                    pass
            
        return cls

    def __getitem__(self, args):
        if not isinstance(args, tuple):
            args = (args,)

        sub, = args
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
                    def generate(d):
                        strat_gen = functools.partial(strat_origin.generate, d)
                        return strat_gen(*params)
                
                StratMeta.__strats__[t] = _GenStrat
                return _GenStrat
            except AttributeError:
                raise TypeError('Cannot get Strategy instance for ~{}, not a typing.Generic instance'.format(t))
        raise TypeError('Cannot get Strategy instance for ~{}'.format(t))
                    
class Strategy(metaclass=StratMeta): 
    '''A :class:`Strategy` is a method of generating values of some type
    in a deterministic, gradual way - building smaller values first
    '''
    @abc.abstractstaticmethod
    def generate(depth, *, partial):
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
    def values(cls, depth, guard=None):
        '''Returns the list of values this :class:`Strategy` generates
        for some givne depth 'depth'
        '''
        yield from cls._trie_to_list(cls.generate(depth=depth), depth, max_depth=depth, guard=guard)

    @classmethod
    def _trie_to_list(cls, trie, d, max_depth, guard=None):
        if max_depth == 0:
            for p, l in trie:
                yield from l

        for p, l in trie:
            # yield the partial result
            if p and guard and not guard(p):
                continue

            for v in l:
                yield v

            if p:
                t = cls.generate(partial=p, depth=d)
                yield from cls._trie_to_list(t, d, max_depth=max_depth-1, guard=guard)
