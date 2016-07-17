Writing and using properties
============================

Properties
----------

Properties are the core element of *speccer*. A property can be one of the following property types.

* unit

  + always passes

* empty

  + always fails

* forall(t, f)

  + passes if all values of type t satisfy f

* exists(t, f)

  + passes if any value of type t satisfies f

The *empty* and *unit* properties represent those properties that always fail or always pass respectively.
More interestingly the *forall* and *exists* properties take a type and a function over that type and 
represents either that for all values of that type the function is True or that there exists some value of
that type where the function is True respectively.

Writing a property
------------------

Given a function ``f(x: int) -> bool`` it is possible to see if any ``int``'s satisfy the function by constructing
a forall-quantification with ``forall(int, f)``


Assertions
-------

Speccer comes with a battery of unittest like asserts in the top-level ``speccer`` package import, including:

- assertTrue(a)

  + asserts ``a == True``
- assertFalse(a)

  + asserts ``a == False``
- assertEqual(a, b)

  + asserts ``a == b``
- assertIs(a, b)

  + asserts ``a is b``
- assertNotEqual(a, b)

  + asserts ``a != b``
- assertIsNot(a, b)

  + asserts ``a is not b``
- assertIsNotInstance(a, b)

  + asserts ``not isinstance(a, b)``
- assertIsInstance(a, b)

  + asserts ``isinstance(a, b)``
- assertIn(a, b)

  + asserts ``a in b``

These can be used as-is or are included in the :class:`PropertySet` interface.

.. code::

    import speccer

    def prop_all_ints_are_even():
        return speccer.forall(int, lambda x: speccer.assertEqual(x % 2, 0))

    speccer.spec(3, prop_all_ints_are_even)

    '''
    output:

    .F
    ================================================================================
    Failure
    After 1 call(s) (0 did not meet implication)
    To depth 3
    In property `prop_all_ints_are_even`

    prop_all_ints_are_even.FORALL(int) ->
     counterexample:
      x=1

    reason: 1 != 0

    FAIL
    '''


Using Properties
================

The simplist way of using a property is to pass it to ``spec`` along with a depth to generate test cases to.

.. code:: 

    import speccer

    def f(x):
        '''x is divisible by 2'''
        return x % 2 == 0

    prop = speccer.forall(int, f)   # all int's are divisible by 2
    speccer.spec(3, prop)  # test to depth 3

    '''
    output:

    .F
    ================================================================================
    Failure
    After 1 call(s) (0 did not meet implication)
    To depth 3
    In property `<stdin>.<module>`

    <stdin>.<module>.FORALL(int) ->
     counterexample:
      x=1

    FAIL
    '''

Property Sets
-------------

Often there'll be many, similar properties that can be grouped together into one. This is what 
:class:`speccer.PropertySet`'s are for. To create a property set just create a class that 
inherits from :class:`speccer.PropertySet` and simply define functions prefixed with ``prop_``
or just bind names to actual :class:`speccer.Property` instances.

.. code:: 

    import speccer

    class PSet(speccer.PropertySet):
        def prop_thing(self):
            return speccer.forall(int, lambda x: x % 2 == 0)

    speccer.spec(3, PSet)

Composing Properties
--------------------

Alternatively it is possible to compose properties together, and to nest them.

.. code::

    import speccer

    speccer.forall(
        int,
        lambda i: speccer.exists( 
            int,
            lambda j: speccer.assertEqual(i, j)))


Properties can be ``+`` or ``*`` together as OR/AND operations respectively.

.. code::

    import speccer

    def const(x): return lambda *args, **kwargs: x

    p_1 = speccer.forall(int, const(True))
    p_2 = speccer.forall(int, const(False))

    assert isinstance(speccer.spec(3, p_1 + p_2, output=False), speccer.clauses.Success)
    assert isinstance(speccer.spec(3, p_1 * p_2, output=False), speccer.clauses.Failure)
    
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

