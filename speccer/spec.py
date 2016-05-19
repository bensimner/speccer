import sys
import time
import types
import typing
import inspect
import logging
import functools
import traceback
import contextlib
import collections

from ._types import *
from .clauses import *
from .import strategy
from .import model

__all__ = ['spec',
        'PropertySet',
        'exists',
        'forall',
]

log = logging.getLogger('spec')
Result = collections.namedtuple('Result', ['outcome', 'source'])
Failure = lambda source: Result(False, source)
Success = lambda source: Result(True, source)

AssertionSource = None

N = 40
LAYOUT = {
        1 : ['-'*40, '='*40],
        2: '-'*40,
}

def _assert(prop, p, succ_m=None, fail_m='_assert'):
    if not p:
        raise AssertionFailure(fail_m)
    elif prop.enable_assertions:
        if succ_m:
            prop.assertions.append((prop, succ_m))
        else:
            prop.assertions.append((prop, '¬({})'.format(fail_m)))

    return True

def spec(depth, prop_or_prop_set, output=True):
    '''Given some :class:`Property` or :class:`PropertySet` 'prop_or_prop_set'
    test it against inputs to depth 'depth
    and print any found counter example
    '''
    prop_set = prop_or_prop_set
    _prop_or_prop_set = prop_or_prop_set
    if not isinstance(prop_or_prop_set, typing.Iterable):
        ## re-write prop_or_prop_set into a PropertySet
        class pset(PropertySet):
            @functools.wraps(prop_or_prop_set)
            def property_thing(self, *args, **kwargs):
                return _prop_or_prop_set(self, *args, **kwargs)
        prop_set = pset()

    def _go(prop):
        if isinstance(prop, types.FunctionType):
            f = prop
            prop = prop(prop_set)
            prop.name = f.__name__

        prop.prop_set = prop_set

        if not output:
            return run_clause(depth, prop)

        t, *args = prop
        if t == PropertyType.FORALL:
            return handle_forall(depth, prop, simple_header=True)
        elif t == PropertyType.EXISTS:
            return handle_exists(depth, prop, simple_header=True)
        elif t == PropertyType.EMPTY:
            return handle_empty(prop, simple_header=True)

    def _next(prop):
        res = _go(prop)
        if res.outcome:
            if res.source.type == PropertyType.EXISTS:
                print(LAYOUT[1][1])
                print()
        else:
            return False
        return True

    prop_or_prop_set = iter(prop_set)

    if len(prop_set) > 1:
        print('')

    for prop in prop_or_prop_set:
        if not _next(prop):
            break
    else:
        print('')
        print('(OK)')



def handle_empty(prop, simple_header=False):
    if 0 in LAYOUT and not simple_header:
        print(LAYOUT[0])
        print('')

    if simple_header:
        print('-- Property: `{p}`'.format(p=str(prop)))

    print(LAYOUT[1][0])
    print('<empty>')

    if not simple_header:
        print('')
        print('OK.')

    return Success(prop)

def handle_exists(depth, prop, simple_header=False):
    '''A Manual run_exists with output
    '''

    n = 0
    dots = 1
    n_dots = 0
    if not simple_header:
        if 0 in LAYOUT:
            print(LAYOUT[0])
    else:
        print('-- Property: `{p}`'.format(p=str(prop)))

    _, (gen_types, f) = prop
    for result in _run_prop(depth, prop, gen_types, f):
        n += 1
        if result.outcome:
            print('*')
            if not simple_header:
                print(LAYOUT[1][0])

                if strategy.FAILED_IMPLICATION:
                    print('Found witness after {n} call(s) ({} did not meet implication)'.format(strategy.FAILED_IMPLICATION, n=n))
                else:
                    print('Found witness after {n} call(s)'.format(n=n))

                print('In Property `{p}`'.format(p=str(prop)))

            print(LAYOUT[2])
            print('Found Witness:')
            print_result(result)
            if not simple_header:
                print('')
                print('OK.')
            return Success(prop)
        else: 
            if n % dots == 0:
                print('.', flush=True, end='')
                n_dots += 1
            
                if n_dots % N == 0:
                    print('')
                    dots *= 10


    print('E')
    print(LAYOUT[1][1])

    if not simple_header:
        if strategy.FAILED_IMPLICATION:
            print('Ran to {n} call(s) ({} did not meet implication)'.format(strategy.FAILED_IMPLICATION, n=n))
        else:
            print('Ran to {n} call(s)'.format(n=n))
        print('Found no witness to depth {d}'.format(d=depth))
        print('{n}/{n}'.format(n=n))
        print('')
        print('FAIL.')
    else:
        print('')
        print('({n} test cases)'.format(n=n))

    return Failure(prop)
    
def handle_forall(depth, prop, simple_header=False):
    '''A Manual run_forall
    '''
    n = 0
    dots = 1
    n_dots = 0

    if not simple_header:
        if 0 in LAYOUT:
            print(LAYOUT[0])
    else:
        print('-- Property: `{p}`'.format(p=str(prop)))

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

            if not simple_header:
                print('In Property `{p}`'.format(p=str(prop)))

            if not simple_header:
                print(LAYOUT[2])
            else:
                print('')

            print('Found Counterexample:')
            print_result(result)

            if not simple_header:
                print('')
                print('FAIL.')
            else:
                print('')
                print('(FAIL)')
            return Failure(prop)
        
        if n % dots == 0:
            print('.', flush=True, end='')
            n_dots += 1
        
            if n_dots % N == 0:
                print('')
                dots *= 10

    if not simple_header:
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
    else:
        print('')
        print('({n} test cases)'.format(n=n))

    return Success(prop)

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

        # counter instance of BoundArguments
        if counter is not None:
            print('{} ->'.format(clause_to_path(p)))
            for arg_name, v in counter.arguments.items():
                if isinstance(v, model.Partials):
                    print(' {} ='.format(arg_name))
                    print('> {}'.format(v.pretty))
                else:
                    print(' {}={}'.format(arg_name, str(v)))

            print('')

    print('Reason:')
    for ass_src, r in p.assertions:
        if ass_src:
            print('> {}, assert\t{}'.format(clause_to_path(ass_src), r))
        else:
            print('> assert\t{}'.format(r))

    if len(p.assertions) > 0:
        print()

    if isinstance(src.reason, Exception):
        print('> EXCEPTION:')
        e = src.reason
        etype = type(e)
        traceback.print_exception(etype, e, e.__traceback__)
    else:
        print(' {}'.format(src.reason))

def pretty_type(t):
    '''Pretty string of some type
    '''
    try:
        # typing.GenericMeta
        return '{}[{}]'.format(t.__name__, ', '.join(map(pretty_type, t.__parameters__)))
    except AttributeError:
        try:
            # typing.TupleMeta
            if t.__tuple_use_ellipsis__:
                return '{}[{}, ...]'.format(t.__name__, ', '.join(map(pretty_type, t.__tuple_parameters__)))
            else:
                return '{}[{}]'.format(t.__name__, ', '.join(map(pretty_type, t.__tuple_parameters__)))
        except AttributeError:
            try:
                return t.__name__
            except AttributeError:
                return str(t)

def clause_to_path(clause):
    '''Convert a Property clause to a prettyified string
    '''
    location = ''
    p = clause
    while p is not None:
        name = p.name
        type_name = p[0].name
        types = p[1][0]
        if p.name is not None:
            name = '{}::{}({})'.format(name, p[0].name, ', '.join(map(pretty_type,types)))
            if not location:
                location = name
            else:
                location = '{}:{}'.format(name, location)
        else:
            if location:
                location = '{}({}):{}'.format(type_name, ', '.join(map(pretty_type,types)), location)
            else:
                location = '{}({})'.format(type_name, ', '.join(map(pretty_type,types)))
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
    args = _get_args(depth, prop, types, f)
    s = inspect.signature(f)
    while True:
        try:
            argt = next(args)
            bind_argt = s.bind(*argt) 
            prop.counter = bind_argt
        except AssertionFailure as e:
            # Rethink the way THIS works?
            counter = s.bind(e._info['value'])
            reason = '{{{}}}: {}'.format(e._info['src'], e._msg)
            prop.counter = counter
            prop.reason = reason
            yield Failure(prop)
        except StopIteration:
            break
        
        try:
            prop.assertions = []
            prop.prop_set.current_prop = prop
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
        except ImplicationFailure:
            # if trying to evaluate the property throws an ImplicationFailure then 
            # send the ImplicationFailuare to the arg generator to deal with
            args.throw(ImplicationFailure)
            continue
        except Exception as e:
            prop.reason = e
            yield Failure(prop)
        else:
            prop.reason = '`{}` returned true'.format(prop)
            yield Success(prop)

class PropSetMeta(type):
    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        def f(p, name):
            p.name = name
            return p
        props = {f(p,name)
                for name, p in namespace.items()
                if name.startswith('prop') or getattr(p,'__isproperty__',False)}
        cls.__props__ = props
        return cls

class PropertySet(metaclass=PropSetMeta):
    def __init__(self):
        # the currently executing Property
        self.current_prop = None

    # UnitTest style assertions
    def assertThat(self, f, *args, fmt='{name}({argv})', fmt_fail='{name}({argv}) is false'):
        s_args = ', '.join(map(repr,args))
        
        try:
            name = f.__code__.co_name
        except AttributeError:
            name = str(f)

        return _assert(self.current_prop, 
                f(*args), 
                fmt.format(argv=s_args, name=name), 
                fmt_fail.format(argv=s_args, name=name))

    def __iter__(self):
        return iter(self.__props__)

    def __len__(self):
        return len(self.__props__)

    def assertTrue(self, a, fmt='True', fmt_fail='False'):
        return _assert(self.current_prop, a, fmt.format(a=a), fmt_fail.format(a=a))

    def assertFalse(self, a, fmt='False', fmt_fail='True'):
        return _assert(self.current_prop, not a, fmt.format(a=a), fmt_fail.format(a=a))

    def assertEqual(self, a, b, fmt='{a} == {b}', fmt_fail='{a} != {b}'):
        return _assert(self.current_prop, a == b, fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

    def assertIs(self, a, b, fmt='{a} is {b}', fmt_fail='{a} is not {b}'):
        return _assert(self.current_prop, a is b, fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

    def assertNotEqual(self, a, b, fmt='{a} != {b}', fmt_fail='{a} == {b}'):
        return _assert(self.current_prop, a != b, '{} != {}'.format(a=a, b=b), fmt_fail.format(a=a, b=b))

    def assertIsNot(self, a, b, fmt='{a} is not {b}', fmt_fail='{a} is {b}'):
        return _assert(self.current_prop, a is not b, fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

    def assertIsNotInstance(self, a, b, fmt='not isinstance({a}, {b})', fmt_fail='isinstance({a}, {b})'):
        return _assert(self.current_prop, not isinstance(a, b), fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

    def assertIsInstance(self, a, b, fmt='isinstance({a}, {b})', fmt_fail='not isinstance({a}, {b})'):
        return _assert(isinstance(a, b), fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))
