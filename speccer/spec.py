import sys
import time
import types
import inspect
import logging
import traceback
import contextlib
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
        'enable_assertions_logging',
        'exists',
        'forall',
]

log = logging.getLogger('spec')
Result = collections.namedtuple('Result', ['outcome', 'source'])
Failure = lambda source: Result(False, source)
Success = lambda source: Result(True, source)

Assertions = []
AssertionSource = None
AssertionsLog = True

N = 40
LAYOUT = {
        1 : ['-'*40, '='*40],
        2: '-'*40,
}

def _assert(p, succ_m=None, fail_m='_assert'):
    if not p:
        raise AssertionFailure(fail_m)
    elif AssertionsLog:
        if succ_m:
            Assertions.append((AssertionSource, succ_m))
        else:
            Assertions.append((AssertionSource, '¬({})'.format(fail_m)))

    return True

@contextlib.contextmanager
def enable_assertions_logging(enabled=True):
    global AssertionsLog
    log = AssertionsLog
    AssertionsLog = enabled
    yield
    AssertionsLog = log

def spec(depth, prop, output=True):
    '''Given some :class:`Property` 'prop'
    test it against inputs to depth 'depth
    and print any found counter example
    '''

    if isinstance(prop, types.FunctionType):
        f = prop
        prop = prop()
        prop.name = f.__name__

    if not output:
        return run_clause(depth, prop)

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

            print('In Property `{p}`'.format(p=str(prop)))
            print(LAYOUT[2])
            print('Found Witness:')
            print_result(result)
            print('')
            print('OK.')
            break
        else: 
            print('.', flush=True, end='')

        if n % N == 0:
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

            print('In Property `{p}`'.format(p=str(prop)))
            print(LAYOUT[2])
            print('Found Counterexample:')
            print_result(result)
            print('')
            print('FAIL.')
            break
        
        print('.', flush=True, end='')
        if n % N == 0:
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
    '''PrettyPrints the witness/counterexample and source to the screen
    '''
    src = result.source
    parents = []
    
    p = src
    while p:
        parents.append(p)
        p = p.parent
    
    while parents:
        p = parents.pop()
        counter = p.counter

        if counter is not None:
            print('{} ->'.format(clause_to_path(p)))
            if len(counter) == 1:
                if isinstance(counter[0], model.Partials):
                    print('> {}'.format(counter[0].pretty))
                else:
                    s = str(counter[0])
                    print(' {}'.format(s))
            else:
                print(' {}'.format(str(counter)))

            print('')

    print('Reason:')
    for ass_src, r in Assertions:
        if ass_src:
            print('> {}, assert\t{}'.format(clause_to_path(ass_src), r))
        else:
            print('> assert\t{}'.format(r))

    if len(Assertions) > 0:
        print()

    if isinstance(src.reason, Exception):
        print('> EXCEPTION:')
        e = src.reason
        etype = type(e)
        traceback.print_exception(etype, e, e.__traceback__)
    else:
        print(' {}'.format(src.reason))

def clause_to_path(clause):
    location = clause.name + ':' + clause[0].name
    p = clause.parent
    while p is not None:
        location = p.name + ':' + location
        p = p.parent
    return location

def run_clause(depth, clause):
    '''Given some Property clause
    run it and yield all the results
    '''
    t, *args = clause
    if  t == PropertyType.FORALL:
        return run_forall(depth, clause)
    elif t == PropertyType.EXISTS:
        return run_exists(depth, clause)
    elif t == PropertyType.EMPTY:
        return Success('<empty>', clause)
    else:
        raise ValueError('Unknown Clause `{}`'.format(clause))

def run_forall(depth, clause):
    '''Given a forall, run it
    and yield the results
    '''
    _, (gen_types, f) = clause
    for result in _run_prop(depth, clause, gen_types, f):
        if not result.outcome:
            return result

    return Success('forall-true', clause)

def run_exists(depth, clause):
    _, (gen_types, f) = clause
    for result in _run_prop(depth, clause, gen_types, f):
        _, *res = result
        if result.outcome:
            return result

    clause.reason = 'no {} exists that satisfies `{}`'.format(gen_types, clause_to_path(clause))
    clause.counter = None
    return Failure(clause)

def _get_args(depth, prop, types, f):
    strats = []
    with strategy.change_strategies(prop.strategies):
        for t in types:
            strat = strategy.get_strat_instance(t)
            strats.append(strat(depth))

    yield from strategy.generate_args_from_strategies(*strats)

def _run_prop(depth, prop, types, f):
    global Assertions, AssertionSource
    args = _get_args(depth, prop, types, f)
    while True:
        try:
            argt = next(args)
            prop.counter = argt
        except AssertionFailure as e:
            # Rethink the way THIS works?
            counter = (e._info['value'],)
            reason = '{{{}}}: {}'.format(e._info['src'], e._msg)
            prop.counter = counter
            prop.reason = reason
            yield Failure(prop)
        except StopIteration:
            break

        try:
            Assertions = []
            AssertionSource = prop

            v = f(*argt)
            if v == False:
                prop.reason = '{} property returned `False`'.format(clause_to_path(prop))
                yield Failure(prop)
                continue
            elif isinstance(v, Property):
                v.parent = prop
                yield run_clause(depth, v)
                continue
        except AssertionFailure as e:
            prop.reason = e._msg
            yield Failure(prop)
        except Exception as e:
            prop.reason = e
            yield Failure(prop)
        else:
            prop.reason = '`{}` returned true'.format(prop)
            yield Success(prop)
    

# UnitTest style assertions
def assertThat(f, *args, fmt='{name}({argv})', fmt_fail='{name}({argv}) is false'):
    s_args = ', '.join(map(repr,args))
    
    try:
        name = f.__code__.co_name
    except AttributeError:
        name = str(f)

    return _assert(f(*args), fmt.format(argv=s_args, name=name), fmt_fail.format(argv=s_args, name=name))

def assertTrue(a, fmt='True', fmt_fail='False'):
    return _assert(a, fmt.format(a=a), fmt_fail.format(a=a))

def assertFalse(a, fmt='False', fmt_fail='True'):
    return _assert(not a, fmt.format(a=a), fmt_fail.format(a=a))

def assertEqual(a, b, fmt='{a} == {b}', fmt_fail='{a} != {b}'):
    return _assert(a == b, fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertIs(a, b, fmt='{a} is {b}', fmt_fail='{a} is not {b}'):
    return _assert(a is b, fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertNotEqual(a, b, fmt='{a} != {b}', fmt_fail='{a} == {b}'):
    return _assert(a != b, '{} != {}'.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertIsNot(a, b, fmt='{a} is not {b}', fmt_fail='{a} is {b}'):
    return _assert(a is not b, fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertIsNotInstance(a, b, fmt='not isinstance({a}, {b})', fmt_fail='isinstance({a}, {b})'):
    return _assert(not isinstance(a, b), fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertIsInstance(a, b, fmt='isinstance({a}, {b})', fmt_fail='not isinstance({a}, {b})'):
    return _assert(isinstance(a, b), fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))
