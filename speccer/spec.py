import sys
import types
import functools
import traceback

from . import clauses
from . import strategy
from . import model
from . import pset
from . import config

@functools.lru_cache(32)
def _find_ancestors(outcome):
    parents = []
    parent = outcome.child_outcome
    while parent:
        parents.append(parent.prop)
        parent = parent.child_outcome
    return parents

def _print_arg(counter, outfile=sys.stdout):
    for arg, value in counter.arguments.items():
        if isinstance(value, model.Partials):
            outfile.write(' {} =\n'.format(arg))
            outfile.write('> {}\n'.format(value.pretty))
        else:
            outfile.write('  {}={}\n'.format(arg, value))

def _print_reason(outcome, outfile=sys.stdout):
    if outcome.assertions:
        outfile.write(' passed assertions:\n')

        for a in outcome.assertions:
            outfile.write(' >  assert,    {}\n'.format(a))

    if isinstance(outcome, clauses.AssertionCounter):
        outfile.write('\n')
        outfile.write(' failure reason: {}\n'.format(outcome.message))

def _print_parents(outcome, outfile=sys.stdout):
    _parents = _find_ancestors(outcome)
    for p in reversed(_parents):
        outfile.write('{} ->\n'.format(clause_to_path(p)))
        assertions, counter = p.partial
        outfile.write(' with arguments:\n')
        _print_arg(counter, outfile=outfile)

        assertions, _ = p.partial
        if assertions:
            outfile.write(' passed assertions:\n')

            for a in assertions:
                outfile.write(' >  assert,    {}\n'.format(a))

            outfile.write('\n')

def _print_prop_summary(prop, outcome, outfile=sys.stdout):
    name = prop.name
    failed_impl = prop.failed_implications
    depth = outcome.state['depth']
    n = outcome.state['calls']
    outfile.write('After {} call(s) ({} did not meet implication)\n'.format(n, failed_impl))
    outfile.write('To depth {}\n'.format(depth))
    outfile.write('In property `{}`\n'.format(name))
    outfile.write('\n')


def _print_success(prop, depth, success, outfile=sys.stdout):
    outfile.write('-' * 80 + '\n')

    if isinstance(success, clauses.NoCounter):
        outfile.write('Found no counterexample\n')
        _print_prop_summary(prop, success, outfile=outfile)
    elif isinstance(success, clauses.Witness):
        outfile.write('Found witness\n')
        _print_prop_summary(prop, success, outfile=outfile)

        outfile.write('{} ->\n'.format(clause_to_path(success.prop)))
        outfile.write(' witness:\n')
        _print_arg(success.reason, outfile=outfile)
        _print_reason(success, outfile=outfile)
        outfile.write('\n')
        _print_parents(success, outfile=outfile)

    outfile.write('\nOK\n')

def _print_failure(prop, depth, failure, outfile=sys.stdout):
    outfile.write('=' * 80)
    outfile.write('\n')

    outfile.write('Failure\n')
    _print_prop_summary(prop, failure, outfile=outfile)
    outfile.write('{} ->\n'.format(clause_to_path(failure.prop)))
    if isinstance(failure, clauses.Counter):
        outfile.write(' counterexample:\n')
        _print_arg(failure.reason, outfile=outfile)
        _print_reason(failure, outfile=outfile)
    elif isinstance(failure, clauses.UnrelatedException):
        outfile.write(' exception:\n')
        outfile.write('\n')
        e = failure.reason
        traceback.print_exception(type(e), e, e.__traceback__, file=outfile)
    elif isinstance(failure, clauses.NoWitness):
        outfile.write(' no witness.\n')
    outfile.write('\n')
    _print_parents(failure, outfile=outfile)

    outfile.write('\nFAIL\n')

def _pretty_print(prop, depth, outcome, outfile=sys.stdout):
    if isinstance(outcome, clauses.Success):
        _print_success(prop, depth, outcome, outfile=outfile)
    else:
        _print_failure(prop, depth, outcome, outfile=outfile)

def spec(depth, prop, output=True, args=(), outfile=sys.stdout):
    '''Run `speccer` on given :class:`Property` 'prop' or some iterable of properties 'prop'
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
    out = _spec(depth, prop, args=args, outfile=outfile)

    if config.CONFIG.graphviz:
        strategy.generation_graph.render()

    return out

def _spec(depth, prop_or_prop_set, args=(), outfile=sys.stdout):
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
            for p in prop_or_prop_set:
                out = _spec(depth, p, args=args, outfile=outfile)
                if isinstance(out, clauses.Failure):
                    return out

                outfile.write('~' * 80)
                outfile.write('\n')
        except TypeError:
            raise
    return clauses.UnitSuccess(None)  # TODO: Better output for propsets?

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
    d = 1
    dots = 0
    print('(x1)', end='')
    try:
        while True:
            try:
                next(outs)
            except StopIteration:
                raise
            except Exception as e:
                raise StopIteration(clauses.UnrelatedException(prop, e))

            if n % d == 0:
                dots += 1
                print('.', flush=True, end='')

            if n == d*10:
                d *= 10
                print('(x{})'.format(d), flush=True, end='')

            n += 1
            if dots % 80 == 0:
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
    return clause.name

def run_clause(depth, clause):
    '''Given some Property clause
    run it and yield all the results
    '''
    return (yield from clause.run(depth))
