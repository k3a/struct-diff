"""
Structural comparison of two objects.
Based on json-diff javascript package (https://github.com/andreyvit/json-diff)
"""

__version__ = "0.9.0-4"
__copyright__ = """
    Copyright (c) 2015 Andrey Tarantsov
    Copyright (c) 2022 Mario Hros (K3A.me)
"""
__credits__ = ["Andrey Tarantsov", "Mario Hros"]

from .comparator import Comparator, diff
from .formatters import *
