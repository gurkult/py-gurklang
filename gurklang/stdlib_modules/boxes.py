from typing import List, Sequence, TypeVar, Tuple
from ..vm_utils import render_value_as_source, stringify_value
from ..builtin_utils import Module, Fail, make_function, make_simple, raw_function
from ..types import Atom, CallByValue, Code, CodeFlags, Instruction, LockBox, MakeBox, Put, State, UnlockBox, Value, Stack, Scope, Int, Vec


module = Module("boxes")
T, V, S = Tuple, Value, Stack
Z = TypeVar("Z", bound=Stack)


module.add("box", raw_function(MakeBox()))


@module.register("->")
def read_box(state: State, fail: Fail):
    if state.stack is None:
        fail(f"calling `->` on empty stack")
    (box, rest) = state.stack

    if box.tag != "box":
        fail(f"{render_value_as_source(box)} is not a box")

    read_value = state.read_box(box.id)
    return state.with_stack((read_value, rest))


@make_function()
def __change_box(state: State, fail: Fail):
    if state.stack is None or state.stack[1] is None:
        fail(f"calling `<=` on stack too shallow")
    (fn, (box, rest)) = state.infinite_stack()

    if box.tag != "box":
        fail(f"{render_value_as_source(box)} is not a box")

    if fn.tag != "code" and fn.tag != "fn":
        fail(f"{render_value_as_source(fn)} is not a funciton")

    read_value = state.read_box(box.id)
    code = raw_function(LockBox(box.id), Put(read_value), Put(fn), CallByValue(), UnlockBox(box.id))
    return state.with_stack((code, rest))


module.add("<=", raw_function(Put(__change_box), CallByValue(), CallByValue()))
