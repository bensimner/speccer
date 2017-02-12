#!/usr/bin/env python
import cProfile
import pstats
import contextlib
import io
import pathlib
import pytest
import matplotlib.pyplot as plt
from pprint import pprint

p = cProfile.Profile()
p.enable()
pytest.main(['tests/'])
p.disable()

sio = io.StringIO()

stats = pstats.Stats()
stats.load_stats(p.create_stats())

# this is the nicest way to interact between the two
p.dump_stats('profile')
stats.add('profile')

stats.sort_stats('tottime')
w, st = stats.get_print_list(['speccer/speccer',0.1])
labels = []
sizes  = []

T = 0
for f in st:
    T += stats.stats[f][2]

for f in st:
    mname, line, fname = f
    mname_path = pathlib.Path(mname)
    mname = mname_path.parts[-1]
    stat = stats.stats[f]
    prim_call_count, num_calls, tot_time, cum_time, callers = stat
    name = f'{mname}:{fname}({line})'
    labels.append(name)
    sizes.append(tot_time/T)

fig, ax = plt.subplots()
ax.pie(sizes, labels=labels)
ax.axis('equal')

plt.show()
