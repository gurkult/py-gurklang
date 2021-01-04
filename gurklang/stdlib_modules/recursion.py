from typing import Callable, TypeVar, Tuple
from ..vm_utils import render_value_as_source
from ..builtin_utils import BuiltinModule, Fail, make_function, raw_function, make_simple, GurklangModule
from ..types import CallByName, CallByValue, NativeFunction, Put, State, Str, Value, Stack, Scope, Int
import random

module = GurklangModule(
"recursion",
["foldr"],
R"""

{ { (b _ ())     { b }
    (b f (a as)) { b f as foldr a f ! }
  } case
} :foldr jar

""")
