import logging
import logging.config

from . import default_strategies
from .model import Model, command
from .strategy import Strategy, register, has_strat_instance, get_strat_instance
from .ops import values, value_args, implies, mapS
from .spec import spec
from .clauses import empty, exists, forall

from .asserts import (assertTrue, assertFalse, assertThat, assertEqual,
                      assertNotEqual, assertIs, assertIsNot, assertIsInstance)

from . import types

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
