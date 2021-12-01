"""
Standard library modules that aren't built-ins
"""
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from gurklang.builtin_utils import Module
from . import math, inspect, coro, repl_utils, boxes, threading_, strings, recursion, ds_pure, ds, streams, io


modules: "List[Module]" = [
    math.module,
    inspect.module,
    coro.module,
    repl_utils.module,
    boxes.module,
    threading_.module,
    strings.module,
    streams.module,
    io.module,
    recursion.module,
    ds_pure.module,
    ds.module,
]
