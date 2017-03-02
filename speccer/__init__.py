import logging
import logging.config

import sys
import attr

from .default_strategies import *
from .model import *
from .strategy import *
from .ops import *
from .pset import *
from .asserts import *
from .types import *
from .clauses import *
from . import spec as specM

def spec(depth, testable, outfile=sys.stdout):
    '''Runs speccer on some testable type (function, Property)
    '''
    return specM.spec(depth, testable, specM.Options(output_file=outfile))

def enableLogging(debug=False):
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,

        'formatters': {
            'default': {
                'format': '[{asctime}] {levelname}, {name}: {message}',
                'datefmt': '%Y/%m/%d %H:%M:%S',
                'style': '{',
            },
        },

        'handlers': {
            'stdout': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
        },

        'root': {
            'level': logging.DEBUG if debug else logging.INFO,
            'handlers': ['stdout'],
        },
    })
