import speccer
import unittest

__all__ = [
    'PropertySet',
    'unittest_wrapper',
]

def _extend_properties(props, bases):
    for b in bases:
        if getattr(b, '__properties__', False):
            props = props.union(b.__properties__)
            props = _extend_properties(props, b)
    return props


class PSetMeta(type):
    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        props = {
            name
            for name in namespace.keys()
            if name.startswith('prop_') or getattr(getattr(cls, name), '__isproperty__', False)}
        props = _extend_properties(props, bases)
        cls.__properties__ = frozenset(props)
        return cls

    def __iter__(self):
        return iter(self.__properties__)

    def __len__(self):
        return len(self.__properties__)

class PropertySet(metaclass=PSetMeta):
    def __iter__(self):
        return iter(self.__properties__)

    def __len__(self):
        return len(self.__properties__)

def unittest_wrapper(depth):
    def _wrapper(pset):
        class NewPSet(pset, unittest.TestCase):
            pass

        for p in NewPSet.__properties__:
            def _f(self, p=p):
                self.depth = depth
                out = speccer.spec(depth, getattr(self, p), output=False)
                # raise other exceptions out
                if isinstance(out, speccer.UnrelatedException):
                    raise out.reason

                self.assertIsInstance(out, speccer.clauses.Success)

            setattr(NewPSet, 'test_{}'.format(p), _f)

        NewPSet.__name__ = pset.__name__
        NewPSet.__qualname__ = pset.__qualname__
        NewPSet.__module__ = pset.__module__
        return NewPSet
    return _wrapper
