from typing import Tuple

from ..builtin_utils import BuiltinModule, Fail, make_simple
from ..types import Value, Stack, Str, Atom, Vec

module = BuiltinModule("streams")
T, V, S = Tuple, Value, Stack


def make_str_stream(s: str, i: int = 0):
    @make_simple()
    def __str_stream(stack: S, fail: Fail):
        if i < len(s):
            return Str(s[i]), (make_str_stream(s, i + 1), stack)
        else:
            return Atom('stream-end'), (__str_stream, stack)

    return __str_stream


def make_tuple_stream(s: Vec, i: int = 0):
    @make_simple()
    def __tuple_stream(stack: S, fail: Fail):
        if i < len(s):
            return s[i], (make_tuple_stream(s, i + 1), stack)
        else:
            return Atom('stream-end'), (__tuple_stream, stack)

    return __tuple_stream


@module.register_simple('str->stream')
def str_to_stream(stack: T[V, S], fail: Fail):
    s, r = stack
    if s.tag != 'str':
        fail(f'{s} is not a string')
    return make_str_stream(s.value), r


@module.register_simple('tuple->stream')
def tuple_to_stream(stack: T[V, S], fail: Fail):
    s, r = stack
    if s.tag != 'vec':
        fail(f'{s} is not a tuple')
    return make_tuple_stream(s.values), r 