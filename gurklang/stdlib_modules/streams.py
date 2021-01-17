from typing import Tuple

from ..builtin_utils import BuiltinModule, Fail, make_simple
from ..types import Value, Stack, Str, Atom

module = BuiltinModule("streams")
T, V, S = Tuple, Value, Stack


def make_stream(s: str, i: int = 0):
    @make_simple()
    def __str_stream(stack: S, fail: Fail):
        if i < len(s):
            return Str(s[i]), (make_stream(s, i + 1), stack)
        else:
            return Atom('stream-end'), (__str_stream, stack)

    return __str_stream


@module.register_simple('str->stream')
def str_to_stream(stack: T[V, S], fail: Fail):
    s, r = stack
    if s.tag != 'str':
        fail(f'{s} is not a string')
    return make_stream(s.value), r
