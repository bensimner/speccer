import sys
import types
import inspect
import logging
import functools
import traceback
import contextlib

from .clauses import  \
    Property, PropertyType, Success, Failure,  \
    Counter, Witness, NoWitness, NoCounter, \
    EmptySuccess, AssertionCounter, UnrelatedException
from .import strategy
from .import model
from .import utils

__all__ = [
    'spec',
    'assertTrue',
    'assertFalse',
    'assertThat',
    'assertEqual',
    'assertNotEqual',
    'assertIs',
    'assertIsNot',
    'assertIsInstance',
    'assertIsNotInstance',
    'assertIn',
    'change_assertions_log',
]

log = logging.getLogger('spec')
AssertionsLogger = None

# Global vars that aid in pretty-printing
Output = False

@contextlib.contextmanager
def change_assertions_log(log=None):
    global AssertionsLogger
    old_log = AssertionsLogger
    AssertionsLogger = log
    yield
    AssertionsLogger = old_log

def _assert(p, succ_m=None, fail_m='_assert'):
    if not p:
        raise AssertionError(fail_m)
    elif AssertionsLogger is not None:
        if succ_m:
            AssertionsLogger.append(succ_m)
        else:
            AssertionsLogger.append('¬({})'.format(fail_m))

    return True

@functools.lru_cache(32)
def _find_ancestors(outcome):
    parents = []
    parent = outcome.prop.parent
    while parent:
        parents.append(parent)
        parent = parent.parent
    return parents

def _print_arg(counter):
    for arg, value in counter.arguments.items():
        if isinstance(value, model.Partials):
            print(' {} ='.format(arg))
            print('> {}'.format(value.pretty))
        else:
            print('  {}={}'.format(arg, value))

def _print_reason(outcome):
    if outcome.assertions:
        print(' assertions:')

        for a in outcome.assertions:
            print(' > assert,    {}'.format(a))

    if isinstance(outcome, AssertionCounter):
        print('')
        print('reason: {}'.format(outcome.message))

def _print_parents(outcome):
    _parents = _find_ancestors(outcome)
    for p in reversed(_parents):
        print('{} ->'.format(clause_to_path(p)))
        assertions, counter = p.partial
        print(' with arguments:')
        _print_arg(counter)

        assertions, _ = p.partial
        if assertions:
            print(' assertions:')

            for a in assertions:
                print(' > assert,    {}'.format(a))

        print('')

def _print_success(prop, depth, success):
    print('-' * 80)

    name = prop.name
    if isinstance(success, NoCounter):
        print('Found no counterexample')
        print('In property `{}`'.format(name))
    elif isinstance(success, Witness):
        print('Found witness')
        print('In property `{}`'.format(name))

        _print_parents(success)
        print('{} ->'.format(clause_to_path(success.prop)))
        print(' witness:')
        _print_arg(success.reason)
        _print_reason(success)

    print('')
    print('OK.')

def _print_failure(prop, depth, failure):
    print('=' * 80)
    print('Failure in', clause_to_path(failure.prop))
    print('')
    _print_parents(failure)
    print('{} ->'.format(clause_to_path(failure.prop)))
    if isinstance(failure, Counter):
        print(' counterexample:')
        _print_arg(failure.reason)
        _print_reason(failure)

    print('')
    print('FAIL.')

def _pretty_print(prop, depth, outcome):
    if isinstance(outcome, Success):
        _print_success(prop, depth, outcome)
    else:
        _print_failure(prop, depth, outcome)

def spec(depth, prop, output=True, outfile=sys.stdout):
    '''Run `speccer` on given :class:`Property` 'prop'
    to depth 'depth'

    if output=True then print to 'outfile', otherwise just return boolean
    result

    if 'prop' is not a :class:`Property` but rather a function, it will be called
    and metadata transfered

    def f():
        return forall(int, lambda i: i == 1)

    # both of these are valid
    > spec(3, f)
    > spec(3, f())
    '''

    if isinstance(prop, types.FunctionType):
        f = prop
        prop = prop()
        prop.name = f.__name__

    outcome = run_clause(depth, prop)
    if output:
        with contextlib.redirect_stdout(outfile):
            _pretty_print(prop, depth, outcome)

    return outcome

def clause_to_path(clause):
    '''Convert a Property clause to a prettyified string
    '''
    location = ''
    p = clause
    while p is not None:
        type_name = p[0].name
        types = p[1][0]
        name = '{}({})'.format(type_name, ', '.join(map(utils.pretty_type, types)))

        if not location:
            location = name
        else:
            location = '{}::{}'.format(name, location)

        if not p.parent:
            location = '{}.{}'.format(p.name, location)

        p = p.parent
    return location

def run_clause(depth, clause):
    '''Given some Property clause
    run it and yield all the results
    '''
    t, *args = clause
    if t == PropertyType.FORALL:
        return run_forall(depth, clause)
    elif t == PropertyType.EXISTS:
        return run_exists(depth, clause)
    elif t == PropertyType.EMPTY:
        return EmptySuccess(clause)
    else:
        raise ValueError('Unknown Clause `{}`'.format(clause))

def run_forall(depth, clause):
    _, [gen_types, f] = clause
    for result in _run_prop(depth, clause, gen_types, f):
        if isinstance(result, Failure):
            return result
    return NoCounter(clause, result.assertions)

def run_exists(depth, clause):
    _, (gen_types, f) = clause
    for result in _run_prop(depth, clause, gen_types, f):
        if isinstance(result, Success):
            return result
    return NoWitness(clause)

def _get_args(depth, prop, types, f):
    strats = []
    with strategy.change_strategies(prop.strategies):
        for t in types:
            strat = strategy.get_strat_instance(t)
            strats.append(strat(depth))

    yield from strategy.generate_args_from_strategies(*strats)

def _bindings(depth, prop, types, f):
    args = _get_args(depth, prop, types, f)
    s = inspect.signature(f)
    while True:
        try:
            argt = next(args)
        except StopIteration:
            break
        except AssertionError:
            print('[_bindings] AssertionError on next(args) (assumed. ImplicationFailure)')
            continue
        else:
            bind_argt = s.bind(*argt)
            counter = bind_argt
            yield counter

def _run_test(counter, depth, prop, f):
    log = []
    prop.partial = (log, counter)

    if not counter:
        return Failure(prop)

    try:
        with change_assertions_log(log):
            v = f(*counter.args, **counter.kwargs)

        if not v:
            return Counter(prop, counter, assertions=log)
        elif isinstance(v, Property):
            v.parent = prop
            return run_clause(depth, v)
    except AssertionError as e:
        return AssertionCounter(prop, counter, e.args[0], assertions=log)
    except Exception as e:
        return UnrelatedException(e)
    else:
        return Witness(prop, counter, assertions=log)

def _run_prop(depth, prop, types, f):
    '''Given some Property function `f` from Property `prop`
    parametrized over `types` then run `f` on all tuples of type Tuple[*types]
    '''
    for counter in _bindings(depth, prop, types, f):
        yield _run_test(counter, depth, prop, f)

# UnitTest style assertions
def assertThat(f, *args, fmt='{name}({argv})', fmt_fail='{name}({argv}) is false'):
    s_args = ', '.join(map(repr, args))

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
    return _assert(a != b, fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertIsNot(a, b, fmt='{a} is not {b}', fmt_fail='{a} is {b}'):
    return _assert(a is not b, fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertIsNotInstance(a, b, fmt='not isinstance({a}, {b})', fmt_fail='isinstance({a}, {b})'):
    return _assert(not isinstance(a, b), fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertIsInstance(a, b, fmt='isinstance({a}, {b})', fmt_fail='not isinstance({a}, {b})'):
    return _assert(isinstance(a, b), fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertIn(a, b, fmt='{a} in {b}', fmt_fail='{a} not in {b}'):
    return _assert(a in b, fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))
