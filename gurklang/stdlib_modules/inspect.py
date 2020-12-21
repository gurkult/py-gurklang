import pprint
import math

from typing import TypeVar
from ..vm_utils import repr_scope
from ..builtin_utils import Module, Fail
from ..types import Atom, Value, Stack, Scope, Int, Vec


module = Module("inspect")
T, V, S = tuple, Value, Stack
Z = TypeVar("Z", bound=Stack)


@module.register("code-dump")
def code_dump(stack: T[V, S], scope: Scope, fail: Fail):
    (code, rest) = stack
    if code.tag != "code":
        fail(f"{code} is not code")
    pprint.pprint(code.instructions)
    return rest, scope


@module.register("type")
def get_type(stack: T[V, S], scope: Scope, fail: Fail):
    (head, rest) = stack
    return (Atom(head.tag), rest), scope
