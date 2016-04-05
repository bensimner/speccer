# Models.py - Definition of a Model
# author: Ben Simner 

import logging
import inspect
import functools
import itertools
import collections
from typing import List

from . import spec
from .strategy import *
from .error_types import *
from . import default_strategies as default

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

Partial = collections.namedtuple('Partial', ['command', 'args', 'var'])
'''A Partially applied :class:`Command`

It contains the actual :class:`Command` 'command', an iterable of :class:`PartialArg`
arguments and string variable name 'var'
'''

class Partials:
    def __init__(self, model, partials=[]):
        self._partials = partials
        self.model = model
        self.values = None

    def validate(self):
        with spec.enable_assertions_logging(False):
            return self._validate()

    def _validate(self):
        '''Check that the cmds type check
        '''
        log.debug('* validate{{{}}}'.format(pretty_partials(self, sep=';', return_annotation=False)))
        self.model.reset_state()
        self.values = []

        def unwrap_args(args):
            for a in args:
                if isinstance(a.value, ModelMeta.replacement_t):
                    yield self.values[a.value.n]
                else:
                    yield a.value

        for partial in self._partials:
            cmd = partial.command
            args = tuple(unwrap_args(partial.args))
            log.debug('validate({} : {})'.format(cmd, args))

            try:
                if cmd.fpre(self.model, args) == False:
                    log.debug('*** FAIL: Pre-condition False')
                    return False
            except AssertionFailure as e:
                log.debug('*** FAIL: Pre-condition AssertionFailure')
                log.debug('*** {}'.format(e))
                return False

            try:
                v = cmd.fdo(*args) # maybe add `self.model' ?
            except AssertionFailure as e:
                e._info['src'] = '{}_execute'.format(cmd.name)
                raise

            self.values.append(v)
            
            try:
                if cmd.fpost(self.model, args, v) == False:
                    log.debug('*** FAIL: Post-condition False')
                    return False
            except AssertionFailure as e:
                e._info['src'] = '{}_postcondition'.format(cmd.name)
                raise
        
            # if passes post-condition, advance to next state
            self.model.state = cmd.fnext(self.model, args, v)

        log.debug('*** PASS: Valid')
        return True

    def __getitem__(self, i):
        return self._partials[i]

    def __repr__(self):
        if self._partials == []:
            return '<empty>'
        return pretty_partials(self, return_annotation=False, sep=';')

    @property
    def pretty(self):
        if self._partials == []:
            return '<empty>'

        return pretty_partials(self, values=self.values, sep='\n> ', return_annotation=False)

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

def pretty_partials(partials, values=None, return_annotation=True, sep='; '):
    def pretty_str(partial, value=None) -> str:
        name = partial.command.name
        var = partial.var
        args = partial.args
        
        s = name
        li_args = []
        for a in args:
            if isinstance(a.value, ModelMeta.replacement_t):
                li_args.append(partials[a.value.n].var)
            else:
                li_args.append(str(a))

        s = '{s}({})'.format(', '.join(li_args), s=s)

        if var:
            s = '{var} = {s}'.format(var=var, s=s)

        if return_annotation and partial.command.return_annotation:
            s = '{s} :: {rt}'.format(s=s, rt=partial.command.return_annotation.__name__)

        if values:
            s = '{s} -> {v}'.format(s=s, v=value)

        return s

    if values is None:
        return sep.join(map(pretty_str, partials))

    out = []
    for i, p in enumerate(partials):
        try:
            v = values[i]
            out.append(pretty_str(p, value=v))
        except IndexError:
            out.append(pretty_str(p))

    return sep.join(out)

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

        cmdlist = sorted(cmdlist, key=lambda c: c.name)
        cls = super().__new__(mcls, name, bases, namespace)
        cls.__modelcommands__ = tuple(cmdlist)

        cls.Command = type('{}_Command'.format(cls), (), {})
        cls.Commands = type('{}_Commands'.format(cls), (), {})
        def validate(ps: cls.Commands) -> bool:
            '''Given a list of partials 'ps' return True if they're valid
            '''
            return ps.validate()
        cls.validate = validate

        class _CmdStrat(Strategy[cls.Command]):
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

        @mapS(Strategy[List[cls.Command]], register_type=cls.Commands)
        def _PartialStrat(depth, cmds):
            log.debug('_PartialStrat')
            #print('PartialStrat{{{}}}'.format(cmds))

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
                yield Partials(cls(), partials)

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
