from speccer import strategy, ops, PyState

def listify(t, d):
    return list(ops.values(d, t))

def test_ints():
    assert listify(int, 2) == [0, 1, -1, 2, -2]

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