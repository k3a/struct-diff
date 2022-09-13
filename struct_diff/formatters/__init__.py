__all__ = ['FormatterError', 'BaseFormatter', 'colorize',
            'JSONFormatter', 'YAMLFormatter']

from .base import *
from .json import *
from .yaml import *
from ..util import _get_opt, _set_opt

def colorize(diff, opts = None):
    """
    Produces structural diff text with ANSI escape sequences for colored output.
    It is an utility function to keep the API compatibility with json_diff JavaScript library.
    """
    if not opts or _get_opt(opts, 'color', None) is None:
        _set_opt(opts, 'color', True)
    return str(JSONFormatter(diff, opts))