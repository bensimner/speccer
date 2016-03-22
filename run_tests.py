#!/usr/bin/env python
import unittest
import sys
import logging.config

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

from typing import List

def runtests(debug=False):
    enableLogging(debug)
    test_suite = unittest.TestLoader().discover('tests/')
    result = unittest.TextTestRunner().run(test_suite)
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == '__main__':
    runtests(debug=False)
