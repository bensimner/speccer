from .helper import HAS_TYPING

class Nat:
    '''Natural numbers 0, 1, 2, ...
    '''

class Neg:
    '''Negated naturals 0, -1, -2, ...
    '''

class Word2:
    '''Natural numbers up to 2 bits
    '''

class Word4:
    '''Natural numbers up to 4 bits
    '''

class Word8:
    '''Natural numbers up to 4 bits
    '''

if HAS_TYPING:
    import typing

    T = typing.T
    class Permutations(typing.Generic[T]):
        '''Lists of permutations of some type T
        '''
