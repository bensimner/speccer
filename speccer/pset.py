class PSetMeta(type):
    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        props = {
            p
            for name, p in namespace.items()
            if name.startswith('prop') or getattr(p, '__isproperty__', False)}
        cls.__properties__ = frozenset(props)
        return cls

class PropertySet(metaclass=PSetMeta):
    def __iter__(self):
        return iter(self.__properties__)

    def __len__(self):
        return len(self.__properties__)
