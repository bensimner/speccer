#!/usr/bin/env python
try:
    from setuptools import setup, find_packages
    print('Cannot find `setuptools`, defaulting to `distutils`')
except ImportError:
    from distutils.core import setup, find_packages

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='speccer',
    version='0.0.2',
    description='Deterministic property-based testing',
    long_description=long_description,
    author='Ben Simner',
    author_email='bs829@york.ac.uk',
    url='https://github.com/bensimner/speccer',
    packages=find_packages(exclude=('tests', 'docs')),
)
