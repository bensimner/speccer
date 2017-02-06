from speccer.misc import *

def with_return(g, r):
    yield from g
    return r

def from_gen(g):
    xs = []
    try:
        while True:
            xs.append(next(g))
    except StopIteration as e:
        return xs, e.value

def test_with_and_from():
    assert from_gen(with_return(range(3), 2)) == ([0, 1, 2], 2)

def test_intersperse_multi_ranges():
    '''Tests that intersperse reflects the returned values
    '''
    r_range1 = with_return(range(3), 1)
    r_range2 = with_return(range(5), 2)
    insp = intersperse([r_range1, r_range2])
    xs, v = from_gen(insp)
    assert xs == [0, 0, 1, 1, 2, 2, 3, 4,]
    assert v == (1, 2,)

def test_intersperse_multi_ranges_invert():
    '''Test that order of returns is preserved over iteration regardless of order of iteration
    '''
    r_range1 = with_return(range(3), 1)
    r_range2 = with_return(range(7), 2)
    r_range3 = with_return(range(2), 3)
    r_range4 = with_return(range(1), 4)
    insp = intersperse([r_range1, r_range2, r_range3, r_range4])
    xs, v = from_gen(insp)
    assert xs == [0, 0, 0, 0, 1, 1, 1, 2, 2, 3, 4, 5, 6,]
    assert v == (1, 2, 3, 4,)

def test_intersperse_order():
    a = ['a', 'b', 'c']
    b = [0, 1, 2, 3]
    c = [True, False]
    insp = intersperse([a, b, c])
    xs, v = from_gen(insp)
    assert xs == ['a', 0, True, 'b', 1, False, 'c', 2, 3]
    assert v == (None, None, None)
