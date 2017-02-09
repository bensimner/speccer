from speccer import PyState, typeable

TEST_NAMES = True

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

if TEST_NAMES:
    def test_typeable_name_base():
        it = typeable.from_type(int)
        assert it.pretty() == 'int'

if PyState.has_typing:
    import typing

    if TEST_NAMES:
        def test_typeable_name_list():
            it = typeable.from_type(typing.List)
            assert it.pretty() == 'List'

        def test_typeable_name_list_int():
            it = typeable.from_type(typing.List[int])
            assert it.pretty() == 'List[int]'

        def test_typeable_name_tuple():
            it = typeable.from_type(typing.Tuple[int, bool])
            assert it.pretty() == 'Tuple[int, bool]'

        def test_typeable_name_nested():
            it = typeable.from_type(typing.List[typing.List[int]])
            assert it.pretty() == 'List[List[int]]'

    def test_any():
        it = typeable.from_type(typing.Any)
        assert it.typ is typing.Any
        assert it.origin is None
        assert it.arity == 0

    def test_listint():
        it = typeable.from_type(typing.List[int])
        assert it.typ is typing.List[int]
        assert it.origin.typ is typing.List
        assert it.origin.origin is None
        assert it.origin.args == []
        assert it.arity == 0

    def test_listint_convert():
        it = typeable.from_type([int])
        assert it.typ is typing.List[int]
        assert it.origin.typ is typing.List
        assert it.origin.origin is None
        assert it.origin.args == []
        assert it.arity == 0

    def test_setint_convert():
        it = typeable.from_type({int})
        assert it.typ is typing.Set[int]
        assert it.origin.typ is typing.Set
        assert it.origin.origin is None
        assert it.origin.args == []
        assert it.arity == 0

    def test_tuple_convert():
        it = typeable.from_type((int, bool))
        assert it.typ is typing.Tuple[int, bool]
        assert it.origin.typ is typing.Tuple
        assert it.origin.origin is None
        assert it.origin.args == []
        assert it.arity == 0

    def test_convert_nested():
        it = typeable.from_type((int, [bool]))
        assert it.typ is typing.Tuple[int, typing.List[bool]]
        assert it.origin.typ is typing.Tuple
        assert it.origin.args == []
        assert it.origin.origin is None
        args = it.args
        assert len(args) == 2
        assert args[0].typ == int
        assert args[1].typ == typing.List[bool]

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
        assert it.origin.typ is typing.Tuple
        assert it.origin.origin is None
        assert it.origin.args == []
        assert it.arity == 0

    def test_union_instance():
        it = typeable.from_type(typing.Union[int, str])
        assert it.typ is typing.Union[int, str]
        assert it.origin.typ is typing.Union
        assert it.origin.origin is None
        assert it.origin.args == []
        assert it.arity == 0
