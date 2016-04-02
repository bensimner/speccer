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

log = logging.getLogger('spec')
Counter = collections.namedtuple('Counter', ['argt'])
Result = collections.namedtuple('Result', ['outcome', 'counter', 'reason', 'source'])

Assertions = []

LAYOUT = {
        1 : ['-', '='],
        2: '-',
}

def _assert(p, fail_m, succ_m=None):
    if not p:
        raise AssertionFailure(fail_m)
    else:
        if succ_m:
            Assertions.append(succ_m)
        else:
            Assertions.append('¬{{{}}}'.format(fail_m))

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

    if prop.quantifier == Property.FORALL:
        handle_forall(prop, depth, **options)
    else:
        handle_exists(prop, depth, **options)

def handle_exists(prop, depth, **options):
    N = 40
    n = 0
    
    if 0 in LAYOUT:
        print(LAYOUT[0] * N)

    for result in prop(depth, **options):
        n += 1

        if result.outcome:
            print('*')
            print(LAYOUT[1][0] * N)

            if strategy.FAILED_IMPLICATION:
                print('Found witness after {n} call(s) ({} did not meet implication)'.format(strategy.FAILED_IMPLICATION, n=n))
            else:
                print('Found witness after {n} call(s)'.format(n=n))

            print('In Property `{p}`'.format(p=str(result.source)))
            print(LAYOUT[2] * N)
            print('Found Witness:')
            if len(result.counter.argt) == 1:
                if isinstance(result.counter.argt[0], model.Partials):
                    print('> {}'.format(result.counter.argt[0].pretty))
                else:
                    s = str(result.counter.argt[0])
                    print(' {}'.format(s))
            else:
                print(' {}'.format(str(result.counter.argt)))

            print('')
            print('Reason:')
            for r in Assertions:
                print(' {}'.format(r))

            print(' {}'.format(result.reason))
            print('')
            print('OK.')
            break
        else: 
            print('.', end='')

        if n == N:
            print('')
    else:
        print('E')
        print(LAYOUT[1][1] * N)
        if strategy.FAILED_IMPLICATION:
            print('Ran to {n} call(s) ({} did not meet implication)'.format(strategy.FAILED_IMPLICATION, n=n))
        else:
            print('Ran to {n} call(s)'.format(n=n))
        print('Found no witness to depth {d}'.format(d=depth))
        print('{n}/{n}'.format(n=n))
        print('')
        print('FAIL.')
    
def handle_forall(prop, depth, **options):
    N = 40
    n = 0

    if 0 in LAYOUT:
        print(LAYOUT[0] * N)

    for result in prop(depth, **options):
        n += 1

        if not result.outcome:
            print('E')
            print(LAYOUT[1][1] * N)

            if strategy.FAILED_IMPLICATION:
                print('Failure after {n} call(s) ({} did not meet implication)'.format(strategy.FAILED_IMPLICATION, n=n))
            else:
                print('Failure after {n} call(s)'.format(n=n))

            print('In Property `{p}`'.format(p=str(result.source)))
            print(LAYOUT[2] * N)
            print('Found Counterexample:')
            if len(result.counter.argt) == 1:
                if isinstance(result.counter.argt[0], model.Partials):
                    print('> {}'.format(result.counter.argt[0].pretty))
                else:
                    s = str(result.counter.argt[0])
                    print(' {}'.format(s))
            else:
                print(' {}'.format(str(result.counter.argt)))
            print('')
            print('Reason:')
            for r in Assertions:
                print(' {}'.format(r))
            print(' {}'.format(result.reason))
            print('')
            print('FAIL.')
            break
        
        print('.', end='')
        if n == N:
            print('')
    else:
        print('')
        print(LAYOUT[1][0] * N)
        if strategy.FAILED_IMPLICATION:
            print('Ran to {n} call(s) ({} did not meet implication)'.format(strategy.FAILED_IMPLICATION, n=n))
        else:
            print('Ran to {n} call(s)'.format(n=n))
        print('Found no counterexample to depth {d}'.format(d=depth))
        print('{n}/{n}'.format(n=n))
        print('')
        print('OK.')

class Property:
    FORALL = 1
    EXISTS = 2

    def __init__(self, f, quantifier=FORALL):
        self._prop_func = f
        self.quantifier = quantifier
        self.strategies = {}

    @staticmethod
    def exists(f):
        return Property(f, quantifier=Property.EXISTS)

    @staticmethod
    def forall(f):
        return Property(f, quantifier=Property.FORALL)

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
        global FAILED_IMPLICATION, AssertionMode
        FAILED_IMPLICATION = 0
        types = list(map(lambda p: p[1].annotation, self.params))

        strats = []
        with strategy.change_strategies(self.strategies):
            for t in types:
                strat = strategy.get_strat_instance(t)
                strats.append(strat(depth))

        args = strategy.generate_args_from_strategies(*strats)
        while True:
            try:
                argt = next(args)
            except AssertionFailure as e:
                yield Result(False, Counter((e._info['value'],)), '{{{}}}: {}'.format(e._info['src'], e._msg), self)
            except StopIteration:
                break

            try:
                Assertions[:] = []
                v = self._prop_func(*argt)
                if v == False:
                    yield Result(False, Counter(argt), 'Property returned False', self)
                    continue
            except AssertionFailure as e:
                yield Result(False, Counter(argt), e._msg, self)
            except Exception as e:
                yield Result(False, Counter(argt), e, self)
            else:
                yield Result(True, Counter(argt), '`{}` returned true'.format(self), self)

    def __str__(self):
        try:
            return self._prop_func.__code__.co_name
        except AttributeError:
            return self.__name__
    
    def __call__(self, depth, **options):
        self.options = options
        yield from self.check(depth)

# UnitTest style assertions
def assertThat(f, *args, fmt_fail='{name}({argv}) is false'):
    s_args = ', '.join(map(repr,args))
    
    try:
        name = f.__code__.co_name
    except AttributeError:
        name = str(f)

    _assert(f(*args), fmt_fail.format(argv=s_args, name=name))

def assertTrue(a, fmt='True'):
    _assert(not a, fmt.format(a=a))

def assertFalse(a, fmt='False'):
    _assert(a, fmt.format(a=a))

def assertEqual(a, b):
    _assert(a == b, '{} == {}'.format(a, b))

def assertIs(a, b):
    _assert(a is b, '{} is {}'.format(a, b))

def assertNotEqual(a, b, fmt_fail='{a} != {b}'):
    _assert(a != b, fmt_fail.format(a=a, b=b))

def assertIsNot(a, b, fmt_fail='{a} is not {b}'):
    _assert(a is not b, fmt_fail.format(a=a, b=b))

def assertIsNotInstance(a, b):
    _assert(not isinstance(a, b), ' not isinstance({}, {})'.format(a, b))

def assertIsInstance(a, b):
    _assert(isinstance(a, b), 'isinstance({}, {})'.format(a, b))
