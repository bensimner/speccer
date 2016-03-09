import inspect
import collections
import logging

from . import strategy
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
        'ModelProperty',
        'AssertionFailure',
]

Counter = collections.namedtuple('Counter', ['argt'])
Result = collections.namedtuple('Result', ['outcome', 'counter', 'reason', 'source'])

class AssertionFailure(Exception):
    def __init__(self, msg):
        self._msg = msg

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

    N = 20
    n = 0
    
    for p in prop(depth, **options):
        if not p.outcome:
            print('E')
            print('-' * N)
            print('Failure after {n} calls'.format(n=n))
            print('In Property `{p}`'.format(p=str(p.source)))
            print('Found Counterexample:')
            print(' {}'.format(p.counter.argt))
            print('')
            print('Reason:')
            print(' {}'.format(p.reason))
            break
        
        print('.', end='')
        n += 1
        if n == N:
            print('')
    else:
        print('')
        print('-' * N)
        print('Finished')
        print('Found no counterexample to depth {d}'.format(d=depth))
        print('{n}/{n}'.format(n=n))
        print('')
        print('OK')

def validate_partials(initial_state=0):
    '''validate the state transitions
    '''
    current_state = initial_state

    while True:
        partial = yield
        cmd = partial.command
        args = partial.args

        if not cmd.fpre(current_state, args):
            raise StopIteration

        # yield the value from this partial
        v = yield
        current_state = cmd.fnext(args, v)
        
        if not cmd.fpost(args, v):
            raise StopIteration

class Property:
    def __init__(self, f):
        self._prop_func = f

    def check(self, depth):
        '''Check this property up to depth 'depth'
        '''

        sig = inspect.signature(self._prop_func)
        types = list(map(lambda p: p[1].annotation, sig.parameters.items()))
        args = strategy.value_args(depth, *types)
        for argt in args:
            if 'verbose' in self.options and self.options['verbose'] == True:
                print('Trying', argt)

            try:
                v = self._prop_func(*argt)
                if v == False:
                    yield Result(False, Counter(argt), 'Property returned False', self)
            except AssertionFailure as e:
                yield Result(False, Counter(argt), e._msg, self)
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


class ModelProperty(Property):
    def check(self, depth):
        # get signature of model
        sig = inspect.signature(self._prop_func)

# UnitTest style assertions
def assertThat(f, *args, fmt='{name}({argv}) is False-y'):
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
