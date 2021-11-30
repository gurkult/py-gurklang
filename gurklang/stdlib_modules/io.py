from typing import Iterable
from ..builtin_utils import BuiltinModule, Fail, make_simple
from ..types import Atom, Str, Value, Stack, Tuple
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

    
def lines_as_stream(file: Iterable[str]):
    @make_simple()
    def __file_stream(stack: S, fail: Fail):
        return next(map(Str, file), Atom("stream-end")), (__file_stream, stack)

    return __file_stream


@module.register_simple()
def lines(stack: T[V, S], fail: Fail):
    path, rest = stack
    if path.tag == "str":
        return lines_as_stream(Path(path.value).open()), rest
    if path.tag == "atom" and path.value == "in":
        return lines_as_stream(sys.stdin), rest
    fail("lines works on the :in atom and a filepath string")