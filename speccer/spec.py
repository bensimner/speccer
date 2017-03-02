import attr

import sys
import types
import functools
import traceback

from . import clauses
from . import strategy
from . import model
from . import pset
from . import config

@attr.s
class Options:
    verbose = attr.ib(default=False)
    show = attr.ib(default=False)
    args = attr.ib(default=[])
    output_file = attr.ib(default=sys.stdout)

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
            outfile.write('{} {} =\n'.format(arg))
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
        outfile.write('{} ->\n'.format(p.name))
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

        outfile.write('{} ->\n'.format(success.prop.name))
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
    outfile.write('{} ->\n'.format(failure.prop.name))
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

def spec(depth, prop, options):
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
    out = _spec(depth, prop, options=options)

    if config.CONFIG.graphviz:
        strategy.generation_graph.render()

    return out

def _spec(depth, prop_or_prop_set, options):
    if callable(prop_or_prop_set):
        f = prop_or_prop_set
        prop_or_prop_set = prop_or_prop_set(*options.args)
        prop_or_prop_set.name = f.__name__

    if isinstance(prop_or_prop_set, pset.PropertySet):
        prop_or_prop_set.depth = depth

    if isinstance(prop_or_prop_set, clauses.Property):
        return _spec_prop(depth, prop_or_prop_set, options=options)
    else:
        try:
            for p in prop_or_prop_set:
                out = _spec(depth, p, options=options)
                if isinstance(out, clauses.Failure):
                    return out

                options.output_file.write('~' * 80)
                options.output_file.write('\n')
        except TypeError:
            raise
    return clauses.UnitSuccess(None)  # TODO: Better output for propsets?

def _get_outcome(p):
    try:
        while True:
            next(p)
    except StopIteration as e:
        return e.value

def _spec_prop(depth, prop, options):
    # reset property state
    # just incase it has been run before
    outfile = options.output_file
    prop.reset_implications()

    outs = run_clause(depth, prop)
    n = 0
    d = 1
    dots = 0
    passes = []
    try:
        while True:
            try:
                passes.append(next(outs))
            except StopIteration:
                raise
            except Exception as e:
                raise StopIteration(clauses.UnrelatedException(prop, e))

            if n % d == 0:
                dots += 1
                print('.', flush=True, end='', file=outfile)

            if n == d*10:
                d *= 10
                print('(x{})'.format(d), flush=True, end='', file=outfile)

            n += 1
            if dots % 80 == 0:
                print('', file=outfile)
    except StopIteration as e:
        outcome = e.value
        outcome.state['calls'] = n
        outcome.state['depth'] = depth

        if n % d != 0:
            print('…', end='', file=outfile)

        if isinstance(outcome, clauses.UnrelatedException):
            print('E', file=outfile)
        elif isinstance(outcome, clauses.Failure):
            print('F', file=outfile)
        else:
            print('', file=outfile)

        _pretty_print(prop, depth, outcome, outfile=outfile)

    return outcome

def run_clause(depth, clause):
    '''Given some Property clause
    run it and yield all the results
    '''
    return (yield from clause.run(depth))
