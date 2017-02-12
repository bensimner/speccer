#!/usr/bin/env python
import os
import cProfile
import pstats
import pathlib
import pytest
import matplotlib.pyplot as plt

PROFILE_FILE = '.profile'

# profile the test suite
p = cProfile.Profile()
p.enable()
pytest.main(['tests/'])
p.disable()


# this is the nicest way to collect the stats from above
# as far as i can tell
stats = pstats.Stats()
p.dump_stats(PROFILE_FILE)
stats.add(PROFILE_FILE)

# get the top 10% of speccer's runtime
stats.sort_stats('tottime')
w, st = stats.get_print_list(['speccer/speccer'])

def make_pie_from_callers(callers):
    labels, sizes, callbacks = [], [], {}

    T = sum(stats.stats[f][2] for f in callers)
    sorted_callers = list(sorted(callers, reverse=True, key=lambda f: stats.stats[f][2]))

    other_callers, max_callers = [], []
    for f in sorted_callers:
        t  = stats.stats[f][2]
        if t < T*0.01:
            other_callers.append(f)
        else:
            max_callers.append(f)

    for f in max_callers:
        mname, line, fname = f
        mname_path = pathlib.Path(mname)
        module = mname_path.parts[-1]
        stat = stats.stats[f]
        prim_call_count, num_calls, tot_time, cum_time, callers = stat
        name = f'{module}:{fname}(line {line})'
        labels.append(name)
        sizes.append(tot_time/T)
        if callers:
            callbacks[name] = callers

    if len(other_callers) > 0:
        # account for "other"
        other = sum(stats.stats[f][2] for f in other_callers)
        labels.append('other')
        sizes.append(other/T)
        callbacks['other'] = other_callers

    return labels, sizes, callbacks

figs = {}

def make_new_pie_from_callers(callers, call_name=None):
    # plot the stats
    fig, ax = plt.subplots()

    if call_name:
        ax.set_title('Breakdown of {} callees'.format(call_name))

    labels, sizes, callbacks = make_pie_from_callers(callers)
    wedges, _ = ax.pie(sizes, labels=labels)

    for w in wedges:
        w.set_picker(True)

    def onclick(evt):
        l = evt.artist.get_label()
        cb = callbacks[l]
        if cb:
            if l == 'other':
                l = '{}/other'.format(call_name)
            make_new_pie_from_callers(cb, call_name=l)


    fig.canvas.mpl_connect('pick_event', onclick)
    ax.axis('equal')
    plt.show()

make_new_pie_from_callers(st, call_name='speccer test suite')
os.remove(PROFILE_FILE)
plt.show()
