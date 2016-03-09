#!/usr/bin/env python
import unittest
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

def test_model():
    class Q:
        pass

    class TestModel(Model):
        @command
        def new(self, size: int) -> Q:
            return Q()

        @command 
        def enqueue(self, q: Q, v: int):
            pass

        @command
        def dequeue(self, q: Q) -> int:
            pass

    @ModelProperty
    def q_is_valid(test_model: TestModel):
        pass

    print('-----------------')
    print('-----------------')
    vals = TestModel.__partial_strat__.values(3)
    for cmds in vals:
        print('---')
        for cmd in cmds:
            print(pretty_str(cmd))

from typing import List

def runtests(debug=False):
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[{asctime}] {levelname}, {name}: {message}',
                'datefmt': '%Y/%m/%d %H:%M:%S',
                'style': '{',
            },
        },

        'handlers': {
            'stdout': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'default',
                'stream': 'ext://sys.stdout',
            },
        },

        'root': {
            'level': 'DEBUG' if debug else 'INFO',
            'handlers': ['stdout'],
        },
    })

    #test_model()
    unittest.main()

if __name__ == '__main__':
    runtests(debug=False)
