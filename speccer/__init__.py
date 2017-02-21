import logging
import logging.config

import attr

from .default_strategies import *
from .model import *
from .strategy import *
from .ops import *
from .spec import *
from .clauses import *
from .pset import *
from .asserts import *
from .types import *

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
