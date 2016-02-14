import inspect

from . import strategy

def check(prop):
    prop()

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

@Property
def prop_myProp(x: int):
    print('x =', x)

if __name__ == '__main__':
    print(prop_myProp)
    print(list(strategy.values(3, int)))
