# Models.py - Definition of a Model
# author: Ben Simner 

import collections
import itertools
import inspect
import functools
import logging
from typing import List

from .strategy import *
from .types import *
from . import default_strategies as default

def empty(self, *_):
    return True

def empty_state(state, args, v):
    '''the empty state transition function
    '''
    return state

def empty_ctor():
    return 0

Partial = collections.namedtuple('Partial', ['command', 'args', 'var'])
'''A Partially applied :class:`Command`

It contains the actual :class:`Command` 'command', an iterable of :class:`PartialArg`
arguments and string variable name 'var'
'''

class Partials:
    def __init__(self, partials=[]):
        self._partials = partials
        self.values = []

    def __repr__(self):
        return pretty_partials(self._partials, values=self.values, return_annotation=True, sep='\n')

    def __iter__(self):
        return iter(self._partials)

PartialArg = collections.namedtuple('PartialArg', ['value', 'name', 'annotation'])
'''A Partially applied argument
here, name can be None meaning it is just a literal
'''

log = logging.getLogger('model') 

def PartialArg_str(self):
    if self.name:
        return self.name
    return repr(self.value)
PartialArg.__str__ = PartialArg_str

VAR_LENGTH = 3
VAR_NAMES = list(values(VAR_LENGTH, str))

def GET_VAR(i):
    global VAR_LENGTH, VAR_NAMES
    while i >= len(VAR_NAMES):
        VAR_LENGTH += 1
        VAR_NAMES = list(values(VAR_LENGTH, str))
    
    return VAR_NAMES[i]

def pretty_str(partial: Partial, value=None, return_annotation=True) -> str:
    name = partial.command.name
    var = partial.var
    args = partial.args
    
    s = name
    s = '{s}({})'.format(', '.join(map(str, args)), s=s)

    if var:
        s = '{var} = {s}'.format(var=var, s=s)

    if return_annotation and partial.command.return_annotation:
        s = '{s} :: {rt}'.format(s=s, rt=partial.command.return_annotation.__name__)

    if value:
        s = '{s} -> {v}'.format(s=s, v=value)

    return s

def pretty_partials(partials, values=None, return_annotation=True, sep='; '):
    if values is None:
        return sep.join(map(functools.partial(pretty_str, return_annotation=return_annotation), partials))

    return sep.join(pretty_str(p, value=v, return_annotation=return_annotation) for p, v in zip(partials, values))

#TODO:
# split this up so that a Model has a single pre/post/next method
# that the command references.
# so that a model can be passed around instead of command/partial lists?
class Command:
    '''An @property like :class:`Command`
    It acts like @property except instead of getter and setter
    it has pre, post and next for handling state transitions
    and validating current states.

    Given some :class:`Command` 'c', there are accessors for its internal
    methods, ``c.fdo``, ``c.fpre``, ``c.fpost``, ``c.fnext`` for its internal
    command, pre-condition, post-condition and state-transition-function respectively.
    '''

    def __init__(self, fdo, fpre=empty, fpost=empty, fnext=empty_state, fname=None):
        self.fdo = fdo
        self.fpre = fpre
        self.fpost = fpost
        self.fnext = fnext
        self.name = fname or fdo.__code__.co_name

    def pre(self, f):
        '''Precondition for this :class:`Command`
        '''
        return Command(self.fdo, f, self.fpost, self.fnext, self.name)

    def post(self, f):
        return Command(self.fdo, self.fpre, f, self.fnext, self.name)

    def next(self, f):
        return Command(self.fdo, self.fpre, self.fpost, f, self.name)

    # these are helper functions to the type signature of the `fdo` function

    @property
    def signature(self):
        s = inspect.signature(self.fdo) 
        return s

    @property
    def return_annotation(self):
        r = self.signature.return_annotation
        if r is not inspect._empty:
            return r
        return None

    @property
    def parameters(self):
        s = self.signature 
        return s.parameters 

    @property
    def param_types(self):
        for p in self.parameters.values():
            yield p.annotation

    def __get__(self, obj, objtype=None): 
        '''Getting a Command is looking up its `fdo` function
        '''
        if obj is None:
            return self
        return self.fdo

    def __repr__(self):
        return 'Command(fname={})'.format(self.name)

def command(*args):
    '''Decorator to make the function a :class:`Command`.

    Allowing easy definition of pre- and post- conditions as well as
    state transitions in a stateful model.
    '''
    def decorator(f):
        return Command(f)

    return decorator

class ModelMeta(type):
    '''Metaclass of a :class:`Model`
    collects all the Command's up into a set to be accessed later
    '''
    var_t = collections.namedtuple('var', ['name'])
    replacement_t = collections.namedtuple('replacement_t', ['n'])

    def __new__(mcls, name, bases, namespace):
        cmdlist = list()

        for name,value in namespace.items():
            if isinstance(value, Command):
                cmdlist.append(value)

        cls = super().__new__(mcls, name, bases, namespace)
        cls.__modelcommands__ = tuple(cmdlist)

        cls_cmd = type('{}_Commands'.format(cls), (), {})
        class _CmdStrat(Strategy[cls_cmd]):
            '''A Strategy for generating all permutations of valid commands in a model
            '''
            def generate(self, depth):
                for k in cmdlist:
                    yield k

        def _generate_partials(depth, cmds, partials, replacements=collections.defaultdict(list)):
            if len(cmds) == 0:
                yield partials
                return

            k, *ks = cmds
            # generate all possible Partial's for k
            types = list(k.param_types)
            args = collections.deque(value_args(depth, *types))
            while args:
                argt = args.popleft()
                for i, (t, v) in enumerate(zip(types, argt)): 
                    # go back through partials and look for t's
                    # by looking it up in `replacements`
                    if not isinstance(v, ModelMeta.replacement_t):
                        for r in replacements[t]: 
                            args.append(argt[:i] + (r,) + argt[1+i:]) # something like that

                    # No strategy for generating t's
                    # so do not leak this argt to the Partial list
                    if v is MissingStrategyError:
                        break
                else:
                    # add partial
                    partial_args = list(map(lambda v, t: PartialArg(v, None, t), argt, types))
                    partial = Partial(k, partial_args, None)
                    # add partial to replacements
                    new_replacements = collections.defaultdict(list)
                    for key, value in replacements.items():
                        new_replacements[key] = list(value)
                    new_replacements[k.return_annotation].append(ModelMeta.replacement_t(len(partials)))
                    yield from _generate_partials(depth, ks, partials + [partial], new_replacements)

        @mapS(Strategy[List[cls_cmd]], register_type=cls)
        def _PartialStrat(depth, cmds: List[cls_cmd]):
            for partials in _generate_partials(depth, cmds, []):
                var_c = 0
                partials = list(partials) 
                for i, p in enumerate(partials):
                    for j, a in enumerate(p.args):
                        # this arg should reference earlier partial
                        # so replace arg and partial
                        if isinstance(a.value, ModelMeta.replacement_t):
                            n = a.value.n
                            p_replacement = partials[n]
                            var = p_replacement.var

                            if p_replacement.var is None:
                                var = GET_VAR(var_c)
                                partials[n] = p_replacement._replace(var=var)
                                var_c += 1

                            # replace the arg
                            new_args = list(p.args)
                            new_args[j] = a._replace(name=var)
                            partials[i] = p._replace(args=new_args)
                yield Partials(partials)

        @mapS(Strategy[List[cls_cmd]])
        def _PartialStrat2(depth, cmds):
            '''TODO:
            -   Partials should store returned values
            -       so things like 
                                    > a <- new(3) -> Queue(size=3)
                                    > enqueue(a, 1) -> None
                                    > dequeue(a) -> 1
            -       are possible to generate
            - also force use of previously generated values for arguments with no Strategy instance
            '''
            # get list of generators for each paramater
            # for each command in the given partial list of commands
            open_list = collections.deque()

            initial = (cmds, [], 0)
            open_list.append(initial)

            while open_list:
                pp = (ks, partials, var_count) = open_list.popleft()
                partials2 = list(partials) # shallow copy

                if ks == []:
                    yield partials
                    continue

                k, *ks = ks
                types = list(k.param_types)
                arg_tuples = collections.deque(value_args(depth, *types))

                while arg_tuples:
                    arg_tuple = arg_tuples.popleft()
                    for j, (v, t) in enumerate(zip(arg_tuple, types)):
                        if v is MissingStrategyError:
                            go(pp, j, arg_tuple=arg_tuple, open_list=open_list, t=t, arg_tuples=arg_tuples)
                            break # don't allow a MisingStrategyError value to filter through
                        else:
                            pass # TODO: Maybe look up anyway? maybe too computationally expensive - possible loop
                    else:
                        def get_partial(val, t):
                            if isinstance(val, ModelMeta.var_t):
                                return PartialArg(None, val.name, t)
                            return PartialArg(val, None, t)

                        partial_args = list(map(get_partial, arg_tuple, types))
                        partial = Partial(k, partial_args, None)
                        partials2.append(partial) 
                        open_list.append((ks, partials2, var_count))

        cls.__partial_strat__ = _PartialStrat
        return cls

class Model(object, metaclass=ModelMeta):
    '''A :class:`Model` is some state-machine model of 
    some arbitrary API
    '''

    def __init__(self, initial_state=empty_ctor):
        self.initial_state = initial_state()
        self.state = self.initial_state

    @classmethod
    def commands(cls, d):
        '''see :meth:`commands`

        Internally this method creates a generator which operators in pairs
        recieving a state and then yielding a valid `Partial`

        if no such pair exists (i.e. no valid transitions from current state)
        a StopIteration exception is thrown and the generator can cease normally.

        The generator determines the arguments to generate from the given model Strategy instance
        'model_strategy' which generates all commands up to a certain depth
        TODO: that.
        '''

        model_strategy = StratMeta.get_strat_instance(cls)
        yield from model_strategy.values(d)


def is_valid(partials, initial=empty_ctor):
    '''Returns `True` if 'partials' is valid for initial state 'initial()'
    in the model.
    '''
    log.debug('** validate{%s}' % pretty_partials(partials, sep='; '))
    current_state = initial()
    partials.values = []

    def unwrap_args(args):
        log.debug('unrwap_args{{{}}}'.format(list(map(str, args))))
        for a in args:
            log.debug('unrwap{{{}}}'.format(repr(a)))
            if isinstance(a.value, ModelMeta.replacement_t):
                yield partials.values[a.value.n]
            else:
                yield a.value

    for partial in partials:
        cmd = partial.command
        args = tuple(unwrap_args(partial.args))

        try:
            if cmd.fpre(current_state, args) == False:
                log.debug('*** FAIL: Pre-condition False')
                return False
        except AssertionFailure:
            log.debug('*** FAIL: Pre-condition AssertionFailure')
            return False
        except Exception:
            log.debug('*** FAIL: Pre-condition Exception')
            return False

        v = cmd.fdo(*args)
        partials.values.append(v)
        current_state = cmd.fnext(current_state, args, v)
        
        try:
            if cmd.fpost(current_state, args, v) == False:
                log.debug('*** FAIL: Post-condition False')
                return False
        except AssertionFailure:
            log.debug('*** FAIL: Post-condition AssertionFailure')
            return False
        except Exception:
            log.debug('*** FAIL: Post-condition Exception')
            return False
    
    log.debug('*** PASS: Valid')
    return True
