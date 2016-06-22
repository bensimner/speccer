#!/usr/bin/env python3
from speccer import *
from speccer.spec import run_clause
from typing import T, List

class P(PropertySet):
    def prop_myProp(self):
        return exists(int, lambda i: assertNotEqual(i, 3))

    def prop_nestedProp(self):
        return forall(
            int,
            lambda i: forall(
                int,
                lambda j: assertEqual(i, j)))

if __name__ == '__main__':
    spec(3, P)
