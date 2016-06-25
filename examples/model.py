#!/usr/bin/env python3
from speccer import *

class MyList:
    '''A "real" list implementation'''
    def append(self, v):
        ...

    def pop(self):
        ...

class MyModel(Model):
    _STATE = None

    @command
    def new() -> MyList:
        return MyList()

    @command
    def append(a: MyList, v: int) -> None:
        a.append(v)

    @command
    def pop(a: MyList) -> int:
        return a.pop()

    def new_pre(self, args):
        assertIs(self.state, None)

    def new_next(self, args, result):
        return []

    def append_next(self, args, result):
        lst, n = args
        return self.state + [n]

    def pop_pre(self, args):
        assertNotEqual(self.state, [])

    def pop_post(self, args, result):
        assertEqual(result, self.state[0])

    def pop_next(self, args, result):
        self.state.pop()
        return self.state

def prop_model():
    valid_commands_t = implies(MyModel.validate_pre, MyModel.Commands)
    return forall(valid_commands_t, lambda cmds: cmds.is_valid())

if __name__ == '__main__':
    out = spec(6, prop_model)

'''
Sample Output:

>> spec(6, prop_model)
.....F
================================================================================
Failure
After 5 call(s) (20 did not meet implication)
To depth 6
In property `prop_model`

prop_model.FORALL(validate_pre->MyModel_Commands) ->
 counterexample:
 cmds =
> a = MyModel.new()
> MyModel.append(a=a, v=0)
> MyModel.pop(a=a)

reason: {MyModel.pop_postcondition}: None != 0

FAIL
'''
