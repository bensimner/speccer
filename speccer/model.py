# Models.py - Definition of a Model
# author: Ben Simner 

import collections
import itertools
import inspect
import functools
from pprint import pprint

from .strategy import *
from . import default_strategies as default

def empty(self, *_):
    return True

def empty_state(self, args, v):
    '''the empty state transition function
    '''
    return self.state

Partial = collections.namedtuple('Partial', ['command', 'args', 'var'])
'''A Partially applied :class:`Command`

It contains the actual :class:`Command` 'command', an unpackable of :class:`PartialArg`
arguments and string variable name 'var'

s.t. 
    Partial(k, args, v) ~= v <- k(*args)
'''

def Partial_str(self):
    return self.command.name


PartialArg = collections.namedtuple('PartialArg', ['value', 'name', 'annotation']) 
'''A Partially applied argument
here, name can be None meaning it is just a literal
'''

def PartialArg_repr(self):
    if self.name:
        return self.name
    return repr(self.value)

PartialArg.__repr__ = PartialArg_repr

VAR_LENGTH = 1
VAR_NAMES = list(values(VAR_LENGTH, str))


def GET_VAR(i):
    global VAR_LENGTH, VAR_NAMES
    if i >= VAR_LENGTH:
        VAR_LENGTH += 1
        VAR_NAMES = list(values(VAR_LENGTH, str))
    return VAR_NAMES[i]

def pretty_str(partial: Partial) -> str:
    name = partial.command.name
    var = partial.var
    args = partial.args
    
    s = name
    s = '{s}({})'.format(', '.join(map(repr, args)), s=s)

    if var:
        s = '{var} <- {s}'.format(var=var, s=s)

    if partial.command.return_annotation:
        s = '{s} -> {rt}'.format(s=s, rt=partial.command.return_annotation.__name__)

    return s

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
        for p in itertools.islice(self.parameters.values(), 1, None):
            yield p.annotation

    def __get__(self, obj, objtype=None): 
        '''Getting a Command is looking up its `fdo` function
        '''
        if obj is None:
            return self
        return self.fdo

    def __repr__(self):
        return 'Command(fname={})'.format(self.name)

def command(f):
    '''Decorator to make the function 'f' a :class:`Command`.

    Allowing easy definition of pre- and post- conditions as well as
    state transitions in a stateful model.
    '''
    return Command(f)

class ModelMeta(type):
    '''Metaclass of a :class:`Model`
    collects all the Command's up into a set to be accessed later
    '''

    def __new__(mcls, name, bases, namespace):
        cmds = set()

        for name,value in namespace.items():
            if isinstance(value, Command):
                cmds.add(value)

        cls = super().__new__(mcls, name, bases, namespace)
        cls.__modelcommands__ = frozenset(cmds)

        class _ModelStrat(Strategy[cls]):
            '''A Strategy for generating all permutations of valid commands in a model
            '''
            @staticmethod
            def generate(depth, partial=[], max_depth=None):
                for k in cmds:
                    yield (partial+[k]), [partial+[k]]

        cls.__model_strat__ = _ModelStrat

        @map_strategy(cls, _ModelStrat, autoregister=False)
        def _PartialStrat(depth, cmds, max_depth):
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

            #get_param_generator(cmd: Command, depth: int)
            initial = (cmds, [], 0)
            open_list.append(initial)

            while open_list:
                (ks, partials, var_count) = open_list.popleft()
                partials2 = list(partials)

                if ks == []:
                    yield partials
                    continue

                k, *ks = ks

                types = list(k.param_types)

                arg_tuples = collections.deque(value_args(depth, *types))
                possible_replacements = collections.defaultdict(list)
                var_t = collections.namedtuple('var', ['name'])

                def go():
                    for i, p in enumerate(partials):
                        if p.command.return_annotation is t:
                            if p.var is None:
                                # go back and put a var on it
                                partials2 = list(partials)
                                partials2[i] = partials2[i]._replace(var=GET_VAR(var_count))
                                open_list.append(([k]+ks, partials2, var_count+1))
                            else:
                                # put that in arg_tuples
                                arg = var_t(p.var)
                                possible_replacements[t].append(arg)
                                arg_tuples.append(arg_tuple[:j] + (arg,) + arg_tuple[(1+j):])

                while arg_tuples:
                    arg_tuple = arg_tuples.popleft()

                    for j, (v, t) in enumerate(zip(arg_tuple, types)):
                        if v is MissingStrategyError:
                            if t in possible_replacements:
                                for arg in possible_replacements[t]:
                                    arg_tuples.append(arg_tuple[:j] + (arg,) + arg_tuple[1+j:])
                                continue
                            # go back and look for return type of `t' in partials
                            go()
                            break
                    else:
                        def get_partial(val, t):
                            if isinstance(val, var_t):
                                return PartialArg(None, val.name, t)
                            return PartialArg(val, None, t)

                        partial_args = list(map(get_partial, arg_tuple, types))
                        partial = Partial(k, partial_args, None)
                        partials2 = list(partials)
                        partials2.append(partial) 
                        open_list.append((ks, partials2, var_count))

        cls.__partial_strat__ = _PartialStrat
        return cls

class Model(object, metaclass=ModelMeta):
    '''A :class:`Model` is some state-machine model of 
    some arbitrary API
    '''

    def __init__(self, initial_state=0):
        self.initial_state = initial_state
        self.state = initial_state

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

def validate(initial_state=0):
    '''validate the state transitions
    '''
    current_state = initial_state

    while True:
        partial = yield
        cmd = partial.command
        args = partial.args

        if not cmd.fpre(current_state, args):
            raise StopIteration

        v = yield
        current_state = cmd.fnext(args, v)
        
        if not cmd.fpost(args, v):
            raise StopIteration

def test_model():
    class Q:
        pass
    class TestModel(Model):
        @command
        def new(self, size: int) -> Q:
            return Q()

        @command 
        def enqueue(self, q: Q, v: int):
            pass

        @command
        def dequeue(self, q: Q) -> int:
            pass

    print('-----------------')
    print('-----------------')
    vals = TestModel.__partial_strat__.values(3)
    for cmds in vals:
        print('---')
        for cmd in cmds:
            print(pretty_str(cmd))
