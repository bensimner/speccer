#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name = 'speccer',
    version = '0.1',
    packages = ['speccer'],
)
