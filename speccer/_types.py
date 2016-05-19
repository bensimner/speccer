'''Internal types
Holds Exceptions and utilities over those types
'''

class MissingStrategyError(Exception):
    pass

class AssertionFailure(Exception):
    def __init__(self, msg):
        self._msg = msg
        self._info = {}

class ImplicationFailure(Exception):
    pass
