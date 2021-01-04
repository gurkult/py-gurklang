from typing import TypeVar, Tuple
from ..vm_utils import render_value_as_source
from ..builtin_utils import Module, Fail, raw_function
from ..types import CallByName, CallByValue, Put, State, Str, Value, Stack, Scope, Int
import random

module = Module("repl-utils")
T, V, S = Tuple, Value, Stack
Z = TypeVar("Z", bound=Stack)


@module.register_simple()
def stack_repr(stack: T[V, S], fail: Fail):
    (depth, rest) = stack
    if depth.tag != "int":
        fail(f"Depth `{render_value_as_source(depth)}`` is not an integer")

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

    return (Str(representation), rest)


peek_n = raw_function(Put(stack_repr), CallByValue(), CallByName("println"))
module.add("peek-n", peek_n)
module.add("peek", raw_function(Put(Int(8)), Put(peek_n), CallByValue()))


FORGET_PHRASES = (
    "See you later, {}.",
    "{} floats down Lethe...",
    "I'll pretend {} never happened.",
    "Let's never talk about {} again.",
    "Sending {} to the shredder... done.",
    "No more {}.",
)

@module.register()
def forget(state: State, fail: Fail):
    (name, rest) = state.infinite_stack()
    if name.tag != "atom":
        fail(f"{render_value_as_source(name)} is not an atom")
    phrase = random.choice(FORGET_PHRASES)
    print(phrase.format(name.value))
    return state.with_stack(rest).forget_name(name.value)
