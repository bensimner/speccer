# Models.py - Definition of a Model
# author: Ben Simner 

import collections
import itertools
import inspect
from pprint import pprint

from strategy import *
import default_strategies as default

def empty(self):
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

PossibleArgs = collections.namedtuple('PossibleArgs', ['type', 'args'])

def deep_tee(iterator, n=2, typ=tuple):
    try:
        it = iter(iterator)
    except TypeError:
        return None

    deques = [collections.deque() for _ in range(n)]
    _to_throw = collections.namedtuple('_to_throw', ['e'])
    def gen(d):
        while True:
            if not d:
                try:
                    v = next(it)
                except StopIteration:
                    return
                except Exception as e: 
                    for d2 in deques:
                        d2.append(_to_throw(e))
                else:
                    gs = deep_tee(v, n=n, typ=type(v))

                    if gs:
                        for g, d2 in zip(gs, deques):
                            d2.append(g)
                    else:
                        for d2 in deques:
                            d2.append(v)
            v = d.popleft()
            if type(v) == _to_throw:
                raise v.e
            yield v
    try:
        return typ(gen(d) for d in deques)
    except TypeError:
        return (gen(d) for d in deques)

VAR_LENGTH = 1
VAR_NAMES = list(values(str, VAR_LENGTH))


def GET_VAR(i):
    global VAR_LENGTH, VAR_NAMES
    if i >= VAR_LENGTH:
        VAR_LENGTH += 1
        VAR_NAMES = list(values(str, VAR_LENGTH))
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
        s = '{s} -> {rt}'.format(s=s, rt=partial.command.return_annotation)

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

def get_param_generator(cmd: Command, depth: int):
    '''Given a :class:`Command` 'cmd' return a
    generator of generators for each parameter
    at depth 'depth'
    '''

    for name, p in itertools.islice(cmd.parameters.items(), 1, None):
        p = p.annotation
        yield (p, values(p, depth))

def get_param_generators(cmds, depth: int):
    '''Returns a generator of parameter generators
    for the given list of Command 'cmds'
    to some depth 'depth'
    '''
    for cmd in cmds:
        yield get_param_generator(cmd, depth)

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

            print()
            print()
            print('cmds =', *cmds)

            # get list of generators for each paramater
            # for each command in the given partial list of commands
            generators = get_param_generators(cmds, max_depth)

            param_gens = generators
            initial_node = (cmds, param_gens, [], 0)
            open_list = collections.deque()
            open_list.appendleft(initial_node)

            while open_list:
                print('try open_list:', len(open_list))
                (ks, gens, partials, var_count) = open_list.popleft()

                if len(ks) >= 1:
                    k, *ks = ks 
                    gen = next(gens)
                else:
                    print('^yielding, partials=', '; '.join(map(pretty_str,partials)))
                    yield partials
                    continue

                print('expanding', k)
                print('arg len =', len(k.parameters))
                print('partials:')
                pprint(partials)

                # The generator of command argument list generators
                gens, gens_tee = deep_tee(gens)
                gen, gen_tee = deep_tee(gen)
                args = []

                # advance each by 1
                print('//', '; '.join(map(pretty_str, partials)), '->' ,k.name, '->', ks)
                for i, (p, arg_g) in enumerate(gen):
                    possible_args = []
                    arg_g, arg_g_cpy = deep_tee(arg_g)
                    print('/', p)
                    
                    while True:
                        try:
                            arg = next(arg_g)
                            possible_args.append(PartialArg(arg, None, p))
                        except MissingStrategyError as e:
                            print('MissingStrat!', e)
                            # look through partials for anything with type p
                            for p_i, partial in enumerate(partials):
                                if partial.command.return_annotation is p:
                                    print('got a {p}'.format(p=p))
                                    # see if it has a var
                                    if partial.var:
                                        print('it has a var={var}'.format(var=partial.var))
                                        possible_args.append(PartialArg(None, partial.var, p))
                                    else:
                                        print('it has no var')
                                        # make a copy of partials 
                                        # and alter partials_copy[i] to now contain a pointer to p
                                        partials_cpy = list(partials)

                                        print('Partials was:')
                                        pprint(partials)
                                        partials_cpy[p_i] = Partial(partial.command, partial.args, GET_VAR(var_count))

                                        print('Changed partials to:')
                                        pprint(partials_cpy)

                                        gens_tee, gens_copy = deep_tee(gens_tee)
                                        gen_tee, gen_copy = deep_tee(gen_tee)

                                        new_node = ([k] + ks, 
                                                    itertools.chain([gen_tee], gens_tee),
                                                    partials_cpy,
                                                    var_count + 1)

                                        open_list.append(new_node)

                        except StopIteration:
                            print('StopIteration!')
                            break
                   
                    if possible_args != []:
                        args.append(PossibleArgs(p, possible_args))
                    else:
                        break

                if len(args) != len(k.parameters) - 1:
                    print('mismatch')
                    continue

                print('after while')
                d = collections.deque()
                d.append(args)

                while d:
                    args = d.popleft()
                    print('got args:')
                    pprint(args)

                    for i, arg in enumerate(args):
                        if type(arg) == PossibleArgs:
                            for a in arg.args:
                                d.appendleft(args[:i] + [a] + args[i+1:])
                            break
                    else:
                        other_partials = list(partials)
                        other_partials.append(Partial(k, args, None))

                        gens_tee, gens_copy = deep_tee(gens_tee)
                        open_list.append((ks, gens_copy, other_partials, var_count))

                print('after d')
            print('after open_list loop')
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

        raise ValueError
        model_strategy = StratMeta.get_strat_instance(cls)
        cmds = model_strategy.generate(d)

        for n, xs in cmds:
            yield n, xs

def validate(list_of_partial_commands, initial_state=0):
    current_state = initial_state
    for partial in list_of_partial_commands:
        cmd = partial.command
        args = partial.args
        if not cmd.fpre(current_state):
            return False

        current_state = cmd.fnext(*args)
    return True

if __name__ == '__main__':
    class Q:
        pass

    class TestModel(Model):
        @command
        def new(self, size: default.Nat) -> Q:
            return size

        @command 
        def enqueue(self, q: Q, v: default.Nat):
            pass

    print('-----------------')
    print('-----------------')
    vals = list(TestModel.__partial_strat__.values(2))
    for cmds in vals:
        print('---')
        for cmd in cmds:
            print(pretty_str(cmd))
