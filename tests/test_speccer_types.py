from speccer import strategy, _types as types

def test_word_2():
    word2 = strategy.Strategy[types.Word2]

    xs = [list(word2(i)) for i in range(7)]

    assert xs[0] == []
    assert xs[1] == [0]
    assert xs[2] == [0, 1]
    assert xs[3] == [0, 1, 2]
    assert xs[4] == [0, 1, 2, 3]
    assert xs[5] == [0, 1, 2, 3]
    assert xs[6] == [0, 1, 2, 3]

def test_word_4():
    word4 = strategy.Strategy[types.Word4]

    xs = [list(word4(i)) for i in range(18)]
    assert xs[0] == []
    assert xs[-1] == list(range(16))

def test_word_8():
    word8 = strategy.Strategy[types.Word8]

    xs = [word8(i) for i in range(258)]
    assert list(xs[0]) == []
    assert list(xs[-1]) == list(range(256))
