"""
Standard library modules that aren't built-ins
"""
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from gurklang.builtin_utils import Module
from . import math, inspect, coro, repl_utils, boxes, threading_, strings, recursion, ds_pure


modules: "List[Module]" = [
    math.module,
    inspect.module,
    coro.module,
    repl_utils.module,
    boxes.module,
    threading_.module,
    strings.module,

    recursion.module,
    ds_pure.module,
]
