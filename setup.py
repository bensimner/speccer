#!/usr/bin/env python
try:
    from setuptools import setup, find_packages
    print('Cannot find `setuptools`, defaulting to `distutils`')
except ImportError:
    from distutils.core import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='speccer',
    version='0.0.1',
    description='Deterministic property-based testing',
    long_description=readme,
    author='Ben Simner',
    author_email='bs829@york.ac.uk',
    url='https://github.com/bensimner/speccer',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
