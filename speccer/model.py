# model.py - Definition of a Model
# author: Ben Simner

import abc
import logging
import inspect
import collections
from typing import List
from pprint import pprint

from . import spec
from . import asserts
from .strategy import Strategy, values, value_args, mapS
from .error_types import MissingStrategyError, InvalidPartials

__all__ = [
    'Model',
    'command',
]


def empty(self, *_):
    return True

def empty_state(self, args, v):
    '''the empty state transition function
    '''
    return self.state

def empty_ctor():
    return 0

class Partials:
    def __init__(self, model, partials=None):
        self._partials = partials or []
        self.model = model

        self.environment = None
        self.values = None

    def validate_pre(self):
        return self.is_valid(only_check_pre=True)

    def is_valid(self, only_check_pre=False):
        with asserts.change_assertions_log(None):
            return self._validate_partials(only_check_pre=only_check_pre)

    def _unwrap_args(self, args):
        for a in args:
            if isinstance(a, NameArg):
                yield self.environment[a.value]
            else:
                yield a.value

    def _validate_partials(self, only_check_pre=False):
        '''Check that the cmds type check
        '''
        log.debug('* validate{{{}}}'.format(self))
        self.model.reset_state()
        self.values = []
        self.environment = {}

        for partial in self._partials:
            cmd = partial.command
            args = tuple(self._unwrap_args(partial.bindings.values()))
            log.debug('is_valid({} : {})'.format(cmd, args))

            try:
                # precondition can just be `pass` which is not a failure case
                if cmd.fpre(self.model, args) is False:
                    log.debug('*** FAIL: Pre-condition False')
                    return False
            except AssertionError as e:
                log.debug('*** FAIL: Pre-condition AssertionError')
                log.debug('*** {}'.format(e))
                name = '{}_pre'.format(cmd.name)
                raise InvalidPartials(name, e) from e

            try:
                v = cmd.fdo(*args)  # maybe add `self.model' ?
            except AssertionError as e:
                name = '{}_execute'.format(cmd.name)
                raise InvalidPartials(name, e) from e

            if isinstance(partial, NamedPartial):
                self.environment[partial.name] = v

            self.values.append(v)

            if not only_check_pre:
                try:
                    # as with pre-condition can just `pass`
                    if cmd.fpost(self.model, args, v) is False:
                        log.debug('*** FAIL: Post-condition False')
                        return False
                except AssertionError as e:
                    name = '{}_postcondition'.format(cmd.name)
                    raise InvalidPartials(name, e) from e

            # if passes post-condition, advance to next state
            self.model.state = cmd.fnext(self.model, args, v)

        log.debug('*** PASS: Valid')
        return True

    def __len__(self):
        return len(self._partials)

    def __getitem__(self, i):
        return self._partials[i]

    def __str__(self):
        if self._partials == []:
            return '<empty>'
        return ';'.join(list(map(str, self._partials)))

    def __repr__(self):
        name = self.__class__.__qualname__
        args = [repr(self.model), repr(self._partials)]
        argstr = ', '.join(args)
        return '%s(%s)' % (name, argstr)

    @property
    def pretty(self):
        if self._partials == []:
            return '<empty>'

        return '\n> '.join(list(map(str, self._partials)))

    def pprint_code_list(self):
        pprint(self._partials)

    def __iter__(self):
        return iter(self._partials)

log = logging.getLogger('model')

VAR_LENGTH = 0
VAR_NAMES = list(values(VAR_LENGTH, str))

def GET_VAR(i):
    global VAR_LENGTH, VAR_NAMES
    while i >= len(VAR_NAMES):
        VAR_LENGTH += 1
        VAR_NAMES = list(values(VAR_LENGTH, str))

    return VAR_NAMES[i]

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
        self._fdo = fdo
        self._fpre = fpre
        self._fpost = fpost
        self._fnext = fnext

        try:
            self.name = fname or fdo.__qualname__
        except AttributeError:
            self.name = fdo.__code__.co_name

    @property
    def fdo(self):
        return self._fdo

    @property
    def fpre(self):
        return self._fpre

    @fpre.setter
    def fpre(self, v):
        self._fpre = v or self._fpre

    @property
    def fpost(self):
        return self._fpost

    @fpost.setter
    def fpost(self, v):
        self._fpost = v or self._fpost

    @property
    def fnext(self):
        return self._fnext

    @fnext.setter
    def fnext(self, v):
        self._fnext = v or self._fnext

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

    def __call__(self, *args, **kwargs):
        '''
        Call a `Command` object to give values to the arguments
        '''
        sig = self.signature
        binding = sig.bind(*args, **kwargs)
        bindings = collections.OrderedDict()
        for k, v in binding.arguments.items():
            bindings[k] = ValueArg(v)
        return Partial(self, bindings)

    def __get__(self, obj, objtype=None):
        '''Getting a Command is looking up its `fdo` function
        '''
        if obj is None:
            return self
        return self.fdo

    def __repr__(self):
        return self.name

class Partial:
    '''A Partially applied :class:`Command`
    '''

    def __init__(self, command, bindings):
        self.command = command
        self.bindings = bindings

    def __str__(self):
        name = self.command.name
        args = []
        for _name, _val in self.bindings.items():
            args.append('{}={}'.format(_name, str(_val)))
        argstr = ', '.join(args)
        rt = self.command.return_annotation

        if rt and False:
            return '%s(%s) -> %s' % (name, argstr, rt.__name__)

        return '%s(%s)' % (name, argstr)

    def __repr__(self):
        argstr = ', '.join([repr(self.command), repr(self.bindings)])
        return '%s(%s)' % (self.__class__.__name__, argstr)

    def copy(self):
        return Partial(self.command, collections.OrderedDict(self.bindings))

class NamedPartial(Partial):
    def __init__(self, name, command, bindings):
        super().__init__(command, bindings)
        self.name = name
        self.args = [name, command, bindings]

    def __str__(self):
        return '{} = {}'.format(self.name, super().__str__())

    def __repr__(self):
        argstr = ', '.join([repr(self.name), repr(self.command), repr(self.bindings)])
        return '%s(%s)' % (self.__class__.__name__, argstr)

    def copy(self):
        return NamedPartial(self.name, self.command, collections.OrderedDict(self.bindings))

    @staticmethod
    def from_partial(partial, name):
        return NamedPartial(name, partial.command, partial.bindings)

class PartialArg(abc.ABC):
    '''An argument in a `Partial`
    '''

    @abc.abstractproperty
    def value(self):
        '''The argument value
        '''

    @abc.abstractmethod
    def __repr__(self):
        pass

    @abc.abstractmethod
    def __str__(self):
        pass

class ValueArg(PartialArg):
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        '''Gets the value associated with this argument
        '''
        return self._value

    def __repr__(self):
        return 'ValueArg(%s)' % repr(self.value)

    def __str__(self):
        return str(self.value)

class NameArg(PartialArg):
    def __init__(self, name):
        self._name = name

    @property
    def value(self):
        '''Gets the name associated with this argument
        '''
        return self._name

    def __repr__(self):
        return 'NameArg(%s)' % repr(self.value)

    def __str__(self):
        return str(self.value)

def command(f):
    '''Decorator to make the function a :class:`Command`.

    Allowing easy definition of pre- and post- conditions as well as
    state transitions in a stateful model.
    '''
    return Command(f)

class ModelMeta(type):
    '''Metaclass of a :class:`Model`
    collects all the Command's up into a set to be accessed later
    '''
    var_t = collections.namedtuple('var', ['name'])
    replacement_t = collections.namedtuple('replacement_t', ['n'])

    def __new__(mcls, name, bases, namespace):
        cmdlist = list()

        for name, value in namespace.items():
            if isinstance(value, Command):
                # look for _pre, _post and _next methods
                value.fpre = namespace.get(name + '_pre', None)
                value.fpost = namespace.get(name + '_post', None)
                value.fnext = namespace.get(name + '_next', None)
                cmdlist.append(value)

        cmdlist = sorted(cmdlist, key=lambda c: c.name)
        cls = super().__new__(mcls, name, bases, namespace)
        cls.__modelcommands__ = tuple(cmdlist)

        cls.Command = type('{}_Command'.format(cls), (), {})
        cls.Commands = type('{}_Commands'.format(cls.__qualname__), (Partials,), {})

        def is_valid(ps: cls.Commands) -> bool:
            '''Given a list of partials 'ps' return True if they're valid
            '''
            return ps.is_valid()

        def validate_pre(ps: cls.Commands) -> bool:
            '''Given a list of partials 'ps' return True if they're valid
            '''
            return ps.validate_pre()

        cls.is_valid = is_valid
        cls.validate_pre = validate_pre

        class _CmdStrat(Strategy[cls.Command]):
            '''A Strategy for generating all permutations of valid commands in a model
            '''
            def generate(self, depth):
                for k in cmdlist:
                    log.debug('YIELD_4')
                    yield k

        def _generate_partials_from_cmds(depth, remaining_cmds, built_partials, replacements=None):
            replacements = replacements or collections.defaultdict(list)

            # finished all cmds
            if len(remaining_cmds) == 0:
                log.debug('YIELD_3')
                yield built_partials
                return

            cmd, *cmds = remaining_cmds
            types = list(cmd.param_types)
            args = collections.deque(value_args(depth, *types))
            first_pass = True

            while args:
                arg_tuple = args.popleft()
                for i, (t, v) in enumerate(zip(types, arg_tuple)):
                    if first_pass:
                        for r in replacements[t]:
                            replacement = arg_tuple[:i] + (r,) + arg_tuple[1 + i:]
                            args.append(replacement)
                        first_pass = False

                    # catch a missing strategy and do something with it
                    # namely stop trying to generate these partials and try add a replacement there instead
                    if v is MissingStrategyError:
                        break
                else:
                    partial_args = collections.OrderedDict()  # TODO: Wrap this in a BoundArguments
                    for key, value in zip(cmd.parameters, arg_tuple):
                        partial_args[key] = ValueArg(value)
                    partial = Partial(cmd, partial_args)

                    # copy defaultdict to depth 2
                    new_replacements = collections.defaultdict(list)
                    for key, value in replacements.items():
                        new_replacements[key] = list(value)

                    new_replacements[cmd.return_annotation].append(ModelMeta.replacement_t(len(built_partials)))
                    # TODO: Replace (built_partials + [partial]) with something more efficient?
                    # TODO: Restructure this so it's fairer ?
                    log.debug('YIELD_2')
                    yield from _generate_partials_from_cmds(depth, cmds, built_partials + [partial], new_replacements)

        @mapS(Strategy[List[cls.Command]], register_type=cls.Commands)
        def _PartialStrat(depth, cmds):
            log.debug('_PartialStrat')

            for partials in _generate_partials_from_cmds(depth, cmds, []):
                var_c = 0
                partials = partials[:]

                for i, p in enumerate(partials):
                    for j, (name, a) in enumerate(p.bindings.items()):
                        # this arg should reference earlier partial
                        # so replace arg and partial
                        if isinstance(a.value, ModelMeta.replacement_t):
                            n = a.value.n
                            p_replacement = partials[n]

                            # give it a name if it has none
                            if not isinstance(p_replacement, NamedPartial):
                                var = GET_VAR(var_c)
                                partials[n] = NamedPartial.from_partial(p_replacement, var)
                                var_c += 1
                            else:
                                var = p_replacement.name

                            # replace the arg
                            partials[i] = partials[i].copy()
                            partials[i].bindings[name] = NameArg(var)

                yield cls.Commands(cls(), partials)

        cls.__partial_strat__ = _PartialStrat
        return cls

class Model(object, metaclass=ModelMeta):
    '''A :class:`Model` is some state-machine model of
    some arbitrary API
    '''
    def __init__(self):
        self.reset_state()

    def reset_state(self):
        self.state = self._STATE
