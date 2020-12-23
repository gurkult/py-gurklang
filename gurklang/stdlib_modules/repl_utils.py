from typing import TypeVar, Tuple
from ..vm_utils import render_value_as_source
from ..builtin_utils import Module, Fail, raw_function
from ..types import CallByName, CallByValue, Put, Str, Value, Stack, Scope, Int


module = Module("repl-utils")
T, V, S = Tuple, Value, Stack
Z = TypeVar("Z", bound=Stack)


@module.register()
def stack_repr(stack: T[V, S], scope: Scope, fail: Fail):
    (depth, rest) = stack
    if depth.tag != "int":
        fail(f"Depth `{depth}`` is not an integer")

    render = lambda x: x
    s = rest
    for _ in range(depth.value):
        if s is None:
            break
        (head, s) = s  # type: ignore
        # closure gotcha
        render = lambda x, old_repr=render, head=head: old_repr(f"({render_value_as_source(head)} {x})")

    if s is None:
        representation = render("()")
    else:
        representation = render("(...)")

    return (Str(representation), rest), scope


peek_n = raw_function(Put(stack_repr), CallByValue(), CallByName("println"))
module.add("peek-n", peek_n)
module.add("peek", raw_function(Put(Int(8)), Put(peek_n), CallByValue()))
