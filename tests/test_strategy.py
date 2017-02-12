from speccer import strategy, ops, PyState
from speccer.default_strategies import Neg

def listify(t, d):
    return list(ops.values(d, t))

def test_ints():
    assert listify(int, 2) == [0, 1, -1, 2, -2]

def test_negs():
    assert listify(Neg, 2) == [0, -1, -2]

def test_bools():
    assert listify(bool, 10) == [False, True]

if PyState.has_typing:
    import typing

    def test_list_int():
        assert listify(typing.List[int], 2) == [[], [0], [1], [-1], [2], [-2]]

    def test_list_bool():
        assert listify(typing.List[bool], 3) == [[], [False], [True], [False, False], [True, False], [False, True], [True, True]]

    def test_nested_list():
        assert listify(typing.List[typing.List[int]], 2) == [[], [[]], [[0]], [[1]], [[-1]], [[2]], [[-2]]]

    def test_union():
        assert listify(typing.Union[int, str], 3) == [0, 'a', 1, 'b', -1, 'c', 2, 'd', -2, 3, -3]
