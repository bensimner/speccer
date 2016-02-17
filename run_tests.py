#!/usr/bin/env python
import unittest

from speccer import *

class DefaultValuesTestCase(unittest.TestCase):
    '''Test default_strategies
    '''
    def check(self, depth, typ, expected): 
        _gen = values(depth, typ)
        self.assertEqual((yield from _gen), expected)
            
    def test_int(self):
        self.check(3, int, [0, 1, -1, 2, -2])

    def test_str(self):
        self.check(2, str, ["", "a", "b", "aa", "ab", "ba", "bb"])

if __name__ == '__main__':
    #unittest.main()
    test_model()
