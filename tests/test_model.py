from speccer import *
from speccer.model import NamedPartial, NameArg

class Q:
    pass

class TestModel(Model):
    _STATE = ()

    @command
    def new(size: int) -> Q:
        return Q()

    @command
    def enqueue(q: Q, v: int):
        pass

    @command
    def dequeue(q: Q) -> int:
        pass

def contains_valid_names(cmds):
    names = set()
    for k in cmds:
        if isinstance(k, NamedPartial):
            names.add(k.name)

    for k in cmds:
        for n, a in k.bindings.items():
            if isinstance(a, NameArg):
                assertIn(a.value, names)

    return True

@unittest_wrapper(depth=3)
class PSet(PropertySet):
    def prop_test_model_names(self):
        '''All NameArg's exist as a command
        '''
        return forall(
            TestModel.Commands,
            lambda cmds: contains_valid_names(cmds))
