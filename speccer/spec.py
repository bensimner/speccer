import types
import inspect
import logging
import traceback
import collections

from .error_types import *
from .clauses import *
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
        'exists',
        'forall',
]

log = logging.getLogger('spec')
Result = collections.namedtuple('Result', ['outcome', 'counter', 'reason', 'source'])
Failure = lambda counter, reason, source: Result(False, counter, reason, source)
Success = lambda counter, reason, source: Result(True, counter, reason, source)

Assertions = []

N = 40
LAYOUT = {
        1 : ['-'*40, '='*40],
        2: '-'*40,
}

def _assert(p, ass_name='Assert', fail_m='_assert', succ_m=None):
    if not p:
        raise AssertionFailure(fail_m)
    else:
        if succ_m:
            Assertions.append((ass_name,succ_m))
        else:
            Assertions.append((ass_name,'¬{{{}}}'.format(fail_m)))

def spec(depth, prop):
    '''Given some :class:`Property` 'prop'
    test it against inputs to depth 'depth
    and print any found counter example
    '''

    if isinstance(prop, types.FunctionType):
        f = prop
        prop = prop()
        prop.name = f.__name__

    t, *args = prop
    if t == PropertyType.FORALL:
        handle_forall(depth, prop)
    elif t == PropertyType.EXISTS:
        handle_exists(depth, prop)
    elif t == PropertyType.EMPTY:
        handle_empty(prop)

def handle_empty(prop):
    if 0 in LAYOUT:
        print(LAYOUT[0])
        print('')

    print(LAYOUT[1][0])
    print('<empty>')
    print('')
    print('OK.')

def handle_exists(depth, prop):
    '''A Manual run_exists with output
    '''
    n = 0
    if 0 in LAYOUT:
        print(LAYOUT[0])

    _, (gen_types, f) = prop
    for result in _run_prop(depth, prop, gen_types, f):
        n += 1

        if result.outcome:
            print('*')
            print(LAYOUT[1][0])

            if strategy.FAILED_IMPLICATION:
                print('Found witness after {n} call(s) ({} did not meet implication)'.format(strategy.FAILED_IMPLICATION, n=n))
            else:
                print('Found witness after {n} call(s)'.format(n=n))

            print('In Property `{p}`'.format(p=str(result.source)))
            print(LAYOUT[2])
            print('Found Witness:')
            print_result(result)
            print('')
            print('OK.')
            break
        else: 
            print('.', end='')

        if n == N:
            print('')
    else:
        print('E')
        print(LAYOUT[1][1])
        if strategy.FAILED_IMPLICATION:
            print('Ran to {n} call(s) ({} did not meet implication)'.format(strategy.FAILED_IMPLICATION, n=n))
        else:
            print('Ran to {n} call(s)'.format(n=n))
        print('Found no witness to depth {d}'.format(d=depth))
        print('{n}/{n}'.format(n=n))
        print('')
        print('FAIL.')
    
def handle_forall(depth, prop):
    '''A Manual run_forall
    '''
    n = 0

    if 0 in LAYOUT:
        print(LAYOUT[0])

    _, (gen_types, f) = prop
    for result in _run_prop(depth, prop, gen_types, f):
        n += 1

        if not result.outcome:
            print('E')
            print(LAYOUT[1][1])

            if strategy.FAILED_IMPLICATION:
                print('Failure after {n} call(s) ({} did not meet implication)'.format(strategy.FAILED_IMPLICATION, n=n))
            else:
                print('Failure after {n} call(s)'.format(n=n))

            print('In Property `{p}`'.format(p=str(result.source)))
            print(LAYOUT[2])
            print('Found Counterexample:')
            print_result(result)
            print('')
            print('FAIL.')
            break
        
        print('.', end='')
        if n == N:
            print('')
    else:
        print('')
        print(LAYOUT[1][0])
        if strategy.FAILED_IMPLICATION:
            print('Ran to {n} call(s) ({} did not meet implication)'.format(strategy.FAILED_IMPLICATION, n=n))
        else:
            print('Ran to {n} call(s)'.format(n=n))
        print('Found no counterexample to depth {d}'.format(d=depth))
        print('{n}/{n}'.format(n=n))
        print('')
        print('OK.')

def print_result(result):
    if len(result.counter) == 1:
        if isinstance(result.counter[0], model.Partials):
            print('> {}'.format(result.counter[0].pretty))
        else:
            s = str(result.counter[0])
            print(' {}'.format(s))
    else:
        print(' {}'.format(str(result.counter)))

    print('')
    print('Reason:')
    for name,r in Assertions:
        print('> {}\t{}'.format(name,r))

    if isinstance(result.reason, Exception):
        print('> EXCEPTION:')
        e = result.reason
        etype = type(e)
        traceback.print_exception(etype, e, e.__traceback__)
    else:
        print(' {}'.format(result.reason))

def run_clause(depth, clause):
    '''Given some Property clause
    run it and yield all the results
    '''
    t, *args = clause
    if  t == PropertyType.FORALL:
        return run_forall(clause)
    elif t == PropertyType.EXISTS:
        return run_exists(clause)
    elif t == PropertyType.EMPTY:
        return Success((), '<empty>', clause)
    else:
        raise ValueError('Unknown Clause `{}`'.format(clause))

def run_forall(depth, clause):
    '''Given a forall, run it
    and yield the results
    '''
    _, (gen_types, f) = clause
    for result in _run_prop(depth, clause, gen_types, f):
        if not result.outcome:
            _, *res = result
            return Failure(*res) # bubble the failure up

    return Success(None, None, None)

def run_exists(depth, clause):
    _, (gen_types, f) = clause
    for result in _run_prop(depth, clause, gen_types, f):
        if result.outcome:
            _, *res = result
            return Success(*res) # bubble success up
    return Failure(None, None, None)

def _get_args(depth, prop, types, f):
    strats = []
    with strategy.change_strategies(prop.strategies):
        for t in types:
            strat = strategy.get_strat_instance(t)
            strats.append(strat(depth))

    yield from strategy.generate_args_from_strategies(*strats)

def _run_prop(depth, prop, types, f):
    # TODO: Rethink AssertionFailures on argt generation and 
    # naming of property down chain (maybe dynamic name or just use topmost?)
    args = _get_args(depth, prop, types, f)
    while True:
        try:
            argt = next(args)
        except AssertionFailure as e:
            # Rethink the way THIS works?
            counter = (e._info['value'],)
            reason = '{{{}}}: {}'.format(e._info['src'], e._msg)
            yield Failure(counter, reason, prop)
        except StopIteration:
            break

        try:
            Assertions[:] = []
            v = f(*argt)
            if v == False:
                yield Failure(argt, 'Property returned False', prop)
                continue
            elif isinstance(v, Property):
                yield run_clause(v)
                continue
        except AssertionFailure as e:
            yield Failure(argt, e._msg, prop)
        except Exception as e:
            yield Failure(argt, e, prop)
        else:
            yield Success(argt, '`{}` returned true'.format(prop), prop)
    

# UnitTest style assertions
def assertThat(f, *args, fmt_fail='{name}({argv}) is false'):
    s_args = ', '.join(map(repr,args))
    
    try:
        name = f.__code__.co_name
    except AttributeError:
        name = str(f)

    _assert(f(*args), 'assertThat', fmt_fail.format(argv=s_args, name=name))

def assertTrue(a, fmt='False'):
    _assert(a, 'assertTrue', fmt.format(a=a))

def assertFalse(a, fmt='True'):
    _assert(not a, 'assertFalse', fmt.format(a=a))

def assertEqual(a, b):
    _assert(a == b, 'assertEqual', '{} != {}'.format(a, b))

def assertIs(a, b):
    _assert(a is b, 'assertIs', '{} is not {}'.format(a, b))

def assertNotEqual(a, b, fmt_fail='{a} == {b}'):
    _assert(a != b, 'assertNotEqual', fmt_fail.format(a=a, b=b))

def assertIsNot(a, b, fmt_fail='{a} is {b}'):
    _assert(a is not b, 'assertIsNot', fmt_fail.format(a=a, b=b))

def assertIsNotInstance(a, b):
    _assert(not isinstance(a, b), 'assertIsNotInstance', 'isinstance({}, {})'.format(a, b))

def assertIsInstance(a, b):
    _assert(isinstance(a, b), 'assertIsInstance', 'not isinstance({}, {})'.format(a, b))
