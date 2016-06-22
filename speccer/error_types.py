class MissingStrategyError(Exception):
    pass

class InvalidPartials(AssertionError):
    def __init__(self, s, e):
        super().__init__('{{{}}}: {}'.format(s, e))
