"""
Standard library modules that aren't built-ins
"""
from ..builtin_utils import Module
from . import math, inspect



modules: list[Module] = [math.module, inspect.module]
