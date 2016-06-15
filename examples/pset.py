#!/usr/bin/env python3
from speccer import *
from speccer.spec import run_clause
from typing import T, List

def prop_myProp():
    return exists(int, lambda i: assertNotEqual(i, 3))

def prop_nestedProp():
    return forall(
        int,
        lambda i: forall(
            int,
            lambda j: assertEqual(i, j)))


if __name__ == '__main__':
    prop = prop_nestedProp()
    spec(3, prop)
