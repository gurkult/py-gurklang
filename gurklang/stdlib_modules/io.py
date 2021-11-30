from ..builtin_utils import BuiltinModule, Fail
from ..types import Str, Value, Stack, Tuple
from pathlib import Path
import sys

module = BuiltinModule('io')

T, V, S = Tuple, Value, Stack

@module.register_simple()
def read(stack: T[V, S], fail: Fail):
    path, rest = stack
    if path.tag == "str":
        return Str(Path(path.value).read_text()), rest
    if path.tag == "atom" and path.value == "in":
        return sys.stdin.read(), rest
    fail("read works on the :in atom and a filepath string")