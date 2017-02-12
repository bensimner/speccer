#!/usr/bin/env python
import cProfile
import pstats
import pathlib
import pytest
import matplotlib.pyplot as plt
from pprint import pprint

# profile the test suite
p = cProfile.Profile()
p.enable()
pytest.main(['tests/'])
p.disable()


# this is the nicest way to collect the stats from above
# as far as i can tell
stats = pstats.Stats()
p.dump_stats('profile')
stats.add('profile')

# get the top 10% of speccer's runtime
stats.sort_stats('tottime')
w, st = stats.get_print_list(['speccer/speccer',0.1])
labels = []
sizes  = []

T = 0
for f in st:
    T += stats.stats[f][2]

other = T*0.1
T = T + other

for f in st:
    mname, line, fname = f
    mname_path = pathlib.Path(mname)
    module = mname_path.parts[-1]
    stat = stats.stats[f]
    prim_call_count, num_calls, tot_time, cum_time, callers = stat
    name = f'{module}:{fname}(line {line})'
    labels.append(name)
    sizes.append(tot_time/T)

# account for "other"
labels.append('other')
sizes.append(other/T)

# plot the stats
fig, ax = plt.subplots()
ax.pie(sizes, labels=labels)
ax.axis('equal')
plt.show()
