"""
Standard library modules that aren't built-ins
"""
from typing import List
from ..builtin_utils import Module
from . import math, inspect, coro, repl_utils, boxes, threading_


modules: List[Module] = [
    math.module,
    inspect.module,
    coro.module,
    repl_utils.module,
    boxes.module,
    threading_.module
]
