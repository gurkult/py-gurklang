from typing import Callable, TypeVar, Tuple
from ..vm_utils import render_value_as_source
from ..builtin_utils import Module, Fail, make_function, raw_function, make_simple
from ..types import CallByName, CallByValue, NativeFunction, Put, State, Str, Value, Stack, Scope, Int
import random

module = Module("strings")
T, V, S = Tuple, Value, Stack
Z = TypeVar("Z", bound=Stack)


@make_simple()
def __foreach_str_init(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (fn, (s, rest)) = stack
    if s.tag != "str":
        fail(f"{render_value_as_source(s)} is not a string")

    if fn.tag != "code" and fn.tag != "native":
        fail(f"{render_value_as_source(fn)} is not a function")

    return (__foreach_str_step, (Int(0), (fn, (s, rest)))), scope

@make_function()
def __foreach_str_step(state: State, fail: Fail) -> State:
    (index, (fn, (s, rest))) = state.infinite_stack()
    assert index.tag == "int"
    assert fn.tag == "code" or fn.tag == "native"
    assert s.tag == "str"

    if index.value >= len(s.value):
        identity = raw_function(source_code="{}")
        return (state
                .with_stack(rest)
                .push(identity)
                .push(identity))

    return (state
            .with_stack(rest)
            .push(s)
            .push(fn)
            .push(Int(index.value + 1))
            .push(__bootstrap_foreach_step)
            .push(Str(s.value[index.value]))
            .push(fn))

__bootstrap_foreach_step = raw_function(
    Put(__foreach_str_step),
    CallByValue(),
    CallByValue(),
    CallByValue(),
    name="--bootstrap-foreach-step"
)
foreach_str = raw_function(
    Put(__foreach_str_init),
    CallByValue(),
    CallByValue(),
    CallByValue(),
    CallByValue(),
    name="foreach-str"
)
module.add("foreach-str", foreach_str)
module.add("∀s", foreach_str)
