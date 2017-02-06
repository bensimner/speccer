from speccer import PyState, typeable

def test_int():
    it = typeable.from_type(int)
    assert it.typ is int
    assert it.origin is None
    assert it.arity == 0

def test_bool():
    it = typeable.from_type(bool)
    assert it.typ is bool
    assert it.origin is None
    assert it.arity == 0

def test_class():
    class C:
        pass

    it = typeable.from_type(C)
    assert it.typ is C
    assert it.origin is None
    assert it.arity == 0

if PyState.has_typing:
    import typing

    def test_any():
        it = typeable.from_type(typing.Any)
        assert it.typ is typing.Any
        assert it.origin is None
        assert it.arity == 0

    def test_listint():
        it = typeable.from_type(typing.List[int])
        assert it.typ is typing.List[int]
        assert it.origin is typing.List
        assert it.arity == 0

    def test_list():
        it = typeable.from_type(typing.List)
        assert it.typ is typing.List
        assert it.origin is None
        assert it.arity == 1

    def test_tuple():
        it = typeable.from_type(typing.Tuple)
        assert it.typ is typing.Tuple
        assert it.origin is None
        assert it.arity == 1

    def test_union():
        it = typeable.from_type(typing.Union)
        assert it.typ is typing.Union
        assert it.origin is None
        assert it.arity == 1

    def test_tuple_intstr():
        it = typeable.from_type(typing.Tuple[int, str])
        assert it.typ is typing.Tuple[int, str]
        assert it.origin is typing.Tuple
        assert it.arity == 0

    def test_union_intstance():
        it = typeable.from_type(typing.Union[int, str])
        assert it.typ is typing.Union[int, str]
        assert it.origin is typing.Union
        assert it.arity == 0