import inspect
import collections
import logging

from .types import *
from .import strategy
from .import model

__all__ = ['spec',
        'assertTrue',
        'assertFalse',
        'assertThat',
        'assertEqual',
        'assertNotEqual',
        'assertIs',
        'assertIsNot',
        'assertIsInstance',
        'assertIsNotInstance',
        'Property',
]

Counter = collections.namedtuple('Counter', ['argt'])
Result = collections.namedtuple('Result', ['outcome', 'counter', 'reason', 'source'])

def _assert(p, m):
    if p:
        raise AssertionFailure(m)

def spec(depth, prop, **options):
    '''Given some :class:`Property` 'prop'
    test it against inputs to depth 'depth
    and print any found counter example

    Options can be as follows:
        verbose:bool    Display generated test cases and stats
    '''

    # TODO: unittest style output?
    # or unittest integration
    # or something?
    if not isinstance(prop, Property):
        print('Warning: Not given Property instance')
        print('Trying to generate one instead')
        prop = Property(prop)
        print('Done...')

    N = 40
    n = 0
    
    for result in prop(depth, **options):
        n += 1

        if not result.outcome:
            print('E')
            print('=' * N)

            if strategy.FAILED_IMPLICATION:
                print('Failure after {n} calls ({} did not meet implication)'.format(strategy.FAILED_IMPLICATION, n=n))
            else:
                print('Failure after {n} calls'.format(n=n))

            print('In Property `{p}`'.format(p=str(result.source)))
            print('-' * N)
            print('Found Counterexample:')
            if len(result.counter.argt) == 1:
                if isinstance(result.counter.argt[0], model.Partials):
                    s = model.pretty_partials(result.counter.argt[0], sep='\n> ', return_annotation=False)
                    print('> {}'.format(s))
                else:
                    s = str(result.counter.argt[0])
                    print(' {}'.format(s))
            else:
                print(' {}'.format(str(result.counter.argt)))
            print('')
            print('Reason:')
            print(' {}'.format(result.reason))
            break
        
        print('.', end='')
        if n == N:
            print('')
    else:
        print('')
        print('-' * N)
        if strategy.FAILED_IMPLICATION:
            print('Ran to {n} calls ({} did not meet implication)'.format(strategy.FAILED_IMPLICATION, n=n))
        else:
            print('Ran to {n} calls'.format(n=n))
        print('Found no counterexample to depth {d}'.format(d=depth))
        print('{n}/{n}'.format(n=n))
        print('')
        print('OK')

class Property:
    def __init__(self, f):
        self._prop_func = f
        self.strategies = {}

    @property
    def params(self):
        sig = inspect.signature(self._prop_func)
        for p in sig.parameters.items():
            yield p

    def check(self, depth):
        '''Check this property up to depth 'depth'
        '''
        # number of failed implications comes from the strategy module
        # might do this a better way?
        global FAILED_IMPLICATION
        FAILED_IMPLICATION = 0
        types = list(map(lambda p: p[1].annotation, self.params))

        strats = []
        with strategy.change_strategies(self.strategies):
            for t in types:
                strat = strategy.get_strat_instance(t)
                strats.append(strat(depth))

        args = strategy.generate_args_from_strategies(*strats)
        for argt in args:
            try:
                v = self._prop_func(*argt)
                if v == False:
                    yield Result(False, Counter(argt), 'Property returned False', self)
            except AssertionFailure as e:
                yield Result(False, Counter(argt), e._msg, self)
            except Exception as e:
                yield Result(False, Counter(argt), e, self)
            else:
                yield Result(True, None, None, None)


    def __str__(self):
        try:
            return self._prop_func.__code__.co_name
        except AttributeError:
            return self.__name__
    
    def __call__(self, depth, **options):
        self.options = options
        yield from self.check(depth)

# UnitTest style assertions
def assertThat(f, *args, fmt='{name}({argv}) is false'):
    s_args = ', '.join(map(repr,args))
    
    try:
        name = f.__code__.co_name
    except AttributeError:
        name = 'f'

    _assert(not f(*args), fmt.format(argv=s_args, name=name))

def assertTrue(a, fmt='{a} is False'):
    _assert(not a, fmt.format(a=a))

def assertFalse(a, fmt='{a} is True'):
    _assert(a, fmt.format(a=a))

def assertEqual(a, b):
    _assert(a != b, '{} != {}'.format(a, b))

def assertIs(a, b):
    _assert(a is not b, '{} is not {}'.format(a, b))

def assertNotEqual(a, b):
    _assert(a == b, '{} == {}'.format(a, b))

def assertIsNot(a, b):
    _assert(a is b, '{} is {}'.format(a, b))

def assertIsNotInstance(a, b):
    _assert(isinstance(a, b), 'isinstance({}, {})'.format(a, b))

def assertIsInstance(a, b):
    _assert(not isinstance(a, b), '¬isinstance({}, {})'.format(a, b))
