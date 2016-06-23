Speccer
=======

*Determinitsic property-based testing in python*


Usage
------------------

Example
^^^^^^^
.. code:: python
    
    from speccer import forall, spec
    from typing import List
    
    def is_sorted(xs):
        return xs == list(sorted(xs))

    def prop_all_lists_are_sorted():
        return forall(List[int], is_sorted)

    >>> spec(4, prop_all_lists_are_sorted)
    ....F
    ================================================================================
    Failure in prop_all_lists_are_sorted.FORALL(List[int])
    prop_all_lists_are_sorted.FORALL(List[int]) ->
     counterexample:
       xs=[1, 0]

    FAIL

Properties
^^^^^^^^^^
The core concept in *speccer* is the *Property*. Each property represents a quantification
over some type (e.g. ``List[int]``) and some function that must hold for all members of that type (e.g. ``is_sorted``).
Once a property exists you can pass it to ``spec``, which will generate test-cases and try to falsify the property. 
Outputting any information as it does so.

a forall quantification can be expressed as follows:

    forall(t, f)

an existential quantification can be expressed as follows:

    exists(t, f)

and they can be nested arbitrarily:

    forall(t, lambda v_t: exists(t2, f))

(If any property's function returns another property, that property is evaluated)

Generation
^^^^^^^^^^

Generation occurs via instances of ``Strategy``. For example:

.. code:: python

    class MyIntStrat(Strategy[int]):
        def generate(self, depth):
            for i in range(depth):
                yield i

When defined as such, it is registered as the new strategy for ``int``'s and can be used immedietely.

    >>> list(values(4, int))  # now uses MyIntStrat
    [0, 1, 2, 3]

Stateful Models
^^^^^^^^^^^^^^^

Sometimes programs have state that mutates. These can be represented as a state machine and modelled that way.

.. code:: python

    class MyArray:
        '''A "real" array implementation'''

    class MyArray_Model(Model):
        @command()
        def 

Theory
------

Random vs Systematic
^^^^^^^^^^^^^^^^^^^^
Traditionally tools that do property-based testing such as QuickCheck_ and Hypothesis_ do by generating large numbers
of random test data with a lot of noise. These tests are not repeatable and invariably get *shrunk* to much smaller test
cases. This is where *speccer* comes in. Speccer takes the approach used in SmallCheck_ to efficiently generate small 
test cases first, deterministically. Giving repeatable tests that **always** give minimal failures.

Future plans include giving an option to perform random tests as well as systematic ones.

Depth Bounded
^^^^^^^^^^^^^
Speccer generates values only up to a given depth. This means lower depth values will be generated first.
Depth is defined as number of nested calls to ``Strategy.generate``.

Future plans include looking into size-bounded enumeration as found in Feat_.

Demand driven generation
^^^^^^^^^^^^^^^^^^^^^^^^
One problem with both random and systematic generation as above is handling implications. For example, generating sorted 
lists by generating all lists and excluding those that are not sorted is woefully inefficient and leaves the user (you) 
scrambling to come up with some complicated system to avoid them. Speccer takes an alterative approach, the generation 
is done as a dispatch on type and so a call to the ``implies(f, t)`` function just returns a new type for which f is
True, and then you can use that to generate new instances. This works by pruning the tree of unwanted nodes and not
evaluting further past there.

.. code:: python

    from speccer import implies, values
    from typing import List

    t_sorted_list = implies(is_sorted, List[int])  # `implies` returns a new type here, which is the type of sorted lists
    for l in values(4, t_sorted_list):  # all sorted lists to depth 4
        print(l)

Not all datatypes are designed for such pruning, and if needed specialised ``Strategy`` instances can be created to 
aid in tree pruning, which can be created as normal.

.. _QuickCheck: https://hackage.haskell.org/package/QuickCheck
.. _Hypothesis: https://pypi.python.org/pypi/hypothesis
.. _SmallCheck: https://hackage.haskell.org/package/smallcheck
.. _Feat: https://hackage.haskell.org/package/testing-feat 

