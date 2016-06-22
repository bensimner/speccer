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
            p
            for name, p in namespace.items()
            if name.startswith('prop_') or getattr(p, '__isproperty__', False)}
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
            def _f(self):
                self.depth = depth
                out = speccer.spec(depth, p, output=False, args=(self,))
                # raise other exceptions out
                if isinstance(out, speccer.UnrelatedException):
                    raise out.reason
                self.assertIsInstance(out, speccer.clauses.Success)

            setattr(pset, 'test_{}'.format(p.__name__), _f)

        NewPSet.__name__ = pset.__name__
        NewPSet.__qualname__ = pset.__qualname__
        NewPSet.__module__ = pset.__module__
        return NewPSet
    return _wrapper
