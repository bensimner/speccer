import sys
import types
import functools
import traceback
import contextlib

from . import clauses
from . import strategy
from . import model
from . import utils
from . import pset
from . import config

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

    if isinstance(outcome, clauses.AssertionCounter):
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

def _print_prop_summary(prop, outcome):
    name = prop.name
    failed_impl = prop.failed_implications
    depth = outcome.state['depth']
    n = outcome.state['calls']
    print('After {} call(s) ({} did not meet implication)'.format(n, failed_impl))
    print('To depth {}'.format(depth))
    print('In property `{}`'.format(name))
    print()


def _print_success(prop, depth, success):
    print('-' * 80)

    if isinstance(success, clauses.NoCounter):
        print('Found no counterexample')
        _print_prop_summary(prop, success)
    elif isinstance(success, clauses.Witness):
        print('Found witness')
        _print_prop_summary(prop, success)

        _print_parents(success)
        print('{} ->'.format(clause_to_path(success.prop)))
        print(' witness:')
        _print_arg(success.reason)
        _print_reason(success)

    print('')
    print('OK')

def _print_failure(prop, depth, failure):
    print('=' * 80)

    print('Failure')
    _print_prop_summary(prop, failure)
    _print_parents(failure)
    print('{} ->'.format(clause_to_path(failure.prop)))
    if isinstance(failure, clauses.Counter):
        print(' counterexample:')
        _print_arg(failure.reason)
        _print_reason(failure)
    elif isinstance(failure, clauses.UnrelatedException):
        print(' exception:')
        print()
        e = failure.reason
        traceback.print_exception(type(e), e, e.__traceback__)
    elif isinstance(failure, clauses.NoWitness):
        print(' no witness.')

    print('')
    print('FAIL')

def _pretty_print(prop, depth, outcome):
    if isinstance(outcome, clauses.Success):
        _print_success(prop, depth, outcome)
    else:
        _print_failure(prop, depth, outcome)

def spec(depth, prop_or_prop_set, output=True, args=(), outfile=sys.stdout):
    '''Run `speccer` on given :class:`Property` 'prop'
    to depth 'depth'

    if output=True then print to 'outfile', otherwise just return boolean
    result

    if 'prop' is not a :class:`Property` but rather a function, it will be called
    and metadata transfered

    args are the arguments to the pass to underlying function/method calls if prop_or_prop_set
    is a function/method or is a PropertySet

    def f():
        return forall(int, lambda i: i == 1)

    # both of these are valid
    > spec(3, f)
    > spec(3, f())
    '''

    with contextlib.redirect_stdout(outfile if output else None):
        out = _spec(depth, prop_or_prop_set, args=args)

    if config.CONFIG.graphviz:
        strategy.generation_graph.render()

    return out

def _spec(depth, prop_or_prop_set, args=()):
    if isinstance(prop_or_prop_set, types.FunctionType) or isinstance(prop_or_prop_set, types.MethodType):
        f = prop_or_prop_set
        prop_or_prop_set = prop_or_prop_set(*args)
        prop_or_prop_set.name = f.__name__

    if isinstance(prop_or_prop_set, pset.PSetMeta):
        prop_or_prop_set = prop_or_prop_set()

    if isinstance(prop_or_prop_set, pset.PropertySet):
        prop_or_prop_set.depth = depth

    if isinstance(prop_or_prop_set, clauses.Property):
        return _spec_prop(depth, prop_or_prop_set)
    else:
        try:
            for p_name in prop_or_prop_set:
                p = getattr(prop_or_prop_set, p_name)
                out = _spec(depth, p, args=args)
                if isinstance(out, clauses.Failure):
                    return out

                print('~' * 80)
        except TypeError:
            raise
    return clauses.UnitSuccess(None, None)  # TODO: Better output for propsets?

def _get_outcome(p):
    try:
        while True:
            next(p)
    except StopIteration as e:
        return e.value

def _spec_prop(depth, prop):
    # reset property state
    # just incase it has been run before
    prop.reset_implications()

    outs = run_clause(depth, prop)
    n = 0
    try:
        while True:
            try:
                next(outs)
            except StopIteration:
                raise
            except Exception as e:
                raise StopIteration(clauses.UnrelatedException(prop, e))

            print('.', flush=True, end='')
            n += 1
            if n % 80 == 0:
                print('')
    except StopIteration as e:
        outcome = e.value
        outcome.state['calls'] = n
        outcome.state['depth'] = depth

        if isinstance(outcome, clauses.UnrelatedException):
            print('E')
        elif isinstance(outcome, clauses.Failure):
            print('F')
        else:
            print('.')

        _pretty_print(prop, depth, outcome)

    return outcome

def clause_to_path(clause):
    location = []
    p = clause
    while p is not None:
        location.append(p.name)
        p = p.parent
    return '.'.join(location)

def _clause_to_path(clause):
    '''Convert a Property clause to a prettyified string
    '''
    location = ''
    p = clause
    while p is not None:
        typ = p.type
        type_name = typ.name
        if typ not in [clauses.PropertyType.FORALL, clauses.PropertyType.EXISTS, ]:
            p = p.parent
            continue

        types = p.args[0]
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
    return (yield from clause.run(depth))
