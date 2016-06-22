#!/usr/bin/env python
import unittest
import sys

from speccer import enableLogging

def runtests(debug=False):
    enableLogging(debug)
    test_suite = unittest.TestLoader().discover('tests/')
    result = unittest.TextTestRunner().run(test_suite)
    sys.exit(0 if result.wasSuccessful() else 1)

if __name__ == '__main__':
    runtests(debug=False)
