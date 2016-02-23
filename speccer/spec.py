import inspect

from . import strategy

def check(prop):
    prop()

def validate_partials(initial_state=0):
    '''validate the state transitions
    '''
    current_state = initial_state

    while True:
        partial = yield
        cmd = partial.command
        args = partial.args

        if not cmd.fpre(current_state, args):
            raise StopIteration

        # yield the value from this partial
        v = yield
        current_state = cmd.fnext(args, v)
        
        if not cmd.fpost(args, v):
            raise StopIteration

class Property:
    def __init__(self, f):
        self._prop_func = f

    def check(self, depth):
        '''Check this property up to depth 'depth'
        '''

        sig = inspect.signature(self._prop_func)

        args = []
        for name, p in sig.parameters.items():
            t = p.annotation
            if t == inspect._empty:
                raise TypeError('Missing type hint on `{}`'.format(name))

            args.append(strategy.values(t, depth))

    def __call__(self, depth):
        self.check(depth)

class ModelProperty(Property):
    def check(self, depth):
        # get signature of model
        sig = inspect.signature(self._prop_func)

@Property
def prop_myProp(x: strategy.Strategy[int]):
    print('x =', x)

if __name__ == '__main__':
    print(prop_myProp)
    print(list(strategy.values(3, int)))
