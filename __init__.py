"""
Structural comparison of two objects.
"""

__version__ = "2.0.0"
__copyright__ = """
    Copyright (c) 2011 Red Hat Corp. (Matěj Cepl)
    Copyright (c) 2022 Mario Hros (K3A.me)
"""
__credits__ = ["Matěj Cepl", "Mario Hros"]

from .comparator import Comparator
from .yaml import YAMLFormatter, YAMLFormatterError