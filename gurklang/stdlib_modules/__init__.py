"""
Standard library modules that aren't built-ins
"""
from gurklang.builtin_utils import GurklangModule, BuiltinModule
from typing import List, Union
from . import math, inspect, coro, repl_utils, boxes, threading_, strings, recursion


modules: List[Union[BuiltinModule, GurklangModule]] = [
    math.module,
    inspect.module,
    coro.module,
    repl_utils.module,
    boxes.module,
    threading_.module,
    strings.module,
    recursion.module,
]
