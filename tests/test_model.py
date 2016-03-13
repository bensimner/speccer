import unittest
from speccer import *

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
    ModelProperty.assertIsValid(test_model)


class TestModelStrat(unittest.TestCase):
    '''Test default_strategies
    '''
    def test_depth_0(self):
        args = [[TestModel.new], [TestModel.enqueue], [TestModel.dequeue]]
        actual = list(values(0, TestModel))
        for a in args:
            self.assertTrue(a in actual)

    def test_depth_1(self):
        actual = list(values(1, TestModel))
        for a in actual:
            self.assertTrue(len(a) < 3)
