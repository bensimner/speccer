import sys
import io
import contextlib

from speccer import spec, unit, empty

def run_spec(depth, p):
    sio = io.StringIO()
    spec(depth, p, outfile=sio)
    return sio.getvalue()

def run_spec_nostdout(depth, p):
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        s = run_spec(depth, p)

    assert stdout.getvalue() == ''
    return s

def test_unit():
    assert 'OK' in run_spec_nostdout(3, unit)

def test_empty():
    assert 'FAIL' in run_spec_nostdout(3, empty)
