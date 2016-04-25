from builtins import tuple as _tuple
import enum
import collections

class PropertyType(enum.Enum):
    FORALL = 1
    EXISTS = 2
    EMPTY = 3

class Property(tuple):
    def __new__(cls, type, args):
        return _tuple.__new__(cls, (type, args))

    def __init__(self, type, args):
        self.strategies = {}
        self.name = None
        self.type = type
        # each Property clause can have a parent clause
        # for nested properties
        self.parent = None

        # each clause can have a counterarguement
        # either counterexample or a witness
        self.counter = None

        # each failure can have a reason string attached
        # with a short description as to why it failed.
        self.reason = None

    def __str__(self):
        return self.name

def empty():
    return Property(PropertyType.EMPTY, [])

def forall(*args):
    '''Forall `type` the function 'f' holds
    where f either returns `bool` or another `Property`
    '''
    *types, f = args
    return Property(PropertyType.FORALL, [types, f])

def exists(*args):
    '''There exists some `type` such that the function 'f' holds
    where f either returns `bool` or another `Property`
    '''
    *types, f = args
    return Property(PropertyType.EXISTS, [types, f])

p = forall(int, lambda x: None)
p = exists(int, p)
