import unittest
from speccer import *

def const(x):
    return lambda *args, **kwargs: x

class ClausesTestCase(unittest.TestCase):
    def setUp(self):
        self.x = forall(int, const(True))
        self.y = forall(int, const(False))

    def test_or(self):
        z = self.x | self.y
        self.assertIsInstance(z, Property)
        self.assertEqual(z[0], PropertyType.OR)

    def test_and(self):
        z = self.x & self.y
        self.assertIsInstance(z, Property)
        self.assertEqual(z[0], PropertyType.AND)

    def test_spec_or(self):
        v = spec(3, self.x & self.y, output=False)
        self.assertIsInstance(v, clauses.Failure)

class TestBaseProperties(unittest.TestCase):
    def test_unit(self):
        self.assertIsInstance(spec(100, unit, output=False), clauses.Success)

    def test_empty(self):
        self.assertIsInstance(spec(100, empty, output=False), clauses.Failure)
