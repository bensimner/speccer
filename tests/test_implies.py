from speccer import values, forall, implies, unittest_wrapper, PropertySet

def is_even(n):
    return n % 2 == 0

@unittest_wrapper(depth=15)
class ImpliesEvens(PropertySet):
    evens = implies(is_even, int)

    def prop_all_even(self):
        '''Idempotence of implies(f)
        '''
        return forall(
            self.evens,
            is_even,
        )

    def prop_all_contained(self):
        vals = values(self.depth, self.evens)
        return forall(
            implies(lambda i: i < self.depth, int),
            lambda i: i in vals if is_even(i) else True,
        )

@unittest_wrapper(depth=15)
class ImpliesInts(PropertySet):
    def prop_all_included(self):
        t = implies(lambda i: i < self.depth, int)
        vals = values(self.depth, t)
        return forall(
            int,
            lambda i: i in vals if i < self.depth else True,
        )
