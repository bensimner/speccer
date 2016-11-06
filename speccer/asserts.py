import logging
import contextlib

__all__ = [
    'assertTrue',
    'assertFalse',
    'assertThat',
    'assertEqual',
    'assertNotEqual',
    'assertIs',
    'assertIsNot',
    'assertIsInstance',
    'assertIsNotInstance',
    'assertIn',
    'change_assertions_log',
]

log = logging.getLogger('spec')
AssertionsLogger = None

@contextlib.contextmanager
def change_assertions_log(log=None):
    global AssertionsLogger
    old_log = AssertionsLogger
    AssertionsLogger = log
    yield
    AssertionsLogger = old_log

def _assert(p, succ_m=None, fail_m='_assert'):
    if not p:
        raise AssertionError(fail_m)
    elif AssertionsLogger is not None:
        if succ_m:
            AssertionsLogger.append(succ_m)
        else:
            AssertionsLogger.append('¬({})'.format(fail_m))

    return True

# UnitTest style assertions
def assertThat(f, *args, fmt='{name}({argv})', fmt_fail='{name}({argv}) is false'):
    s_args = ', '.join(map(repr, args))

    try:
        name = f.__code__.co_name
    except AttributeError:
        name = str(f)

    return _assert(f(*args), fmt.format(argv=s_args, name=name), fmt_fail.format(argv=s_args, name=name))

def assertTrue(a, fmt='True', fmt_fail='False'):
    return _assert(a, fmt.format(a=a), fmt_fail.format(a=a))

def assertFalse(a, fmt='False', fmt_fail='True'):
    return _assert(not a, fmt.format(a=a), fmt_fail.format(a=a))

def assertEqual(a, b, fmt='{a} == {b}', fmt_fail='{a} != {b}'):
    return _assert(a == b, fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertIs(a, b, fmt='{a} is {b}', fmt_fail='{a} is not {b}'):
    return _assert(a is b, fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertNotEqual(a, b, fmt='{a} != {b}', fmt_fail='{a} == {b}'):
    return _assert(a != b, fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertIsNot(a, b, fmt='{a} is not {b}', fmt_fail='{a} is {b}'):
    return _assert(a is not b, fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertIsNotInstance(a, b, fmt='not isinstance({a}, {b})', fmt_fail='isinstance({a}, {b})'):
    return _assert(not isinstance(a, b), fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertIsInstance(a, b, fmt='isinstance({a}, {b})', fmt_fail='not isinstance({a}, {b})'):
    return _assert(isinstance(a, b), fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))

def assertIn(a, b, fmt='{a} in {b}', fmt_fail='{a} not in {b}'):
    return _assert(a in b, fmt.format(a=a, b=b), fmt_fail.format(a=a, b=b))
