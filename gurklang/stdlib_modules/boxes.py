from typing import TypeVar, Tuple
from ..vm_utils import render_value_as_source
from ..builtin_utils import Module, Fail, make_simple, raw_function
from ..types import  CallByValue, Put, State, Value, Stack, Scope


module = Module("boxes")
T, V, S = Tuple, Value, Stack
Z = TypeVar("Z", bound=Stack)


@module.register("box")
def box_(state: State, fail: Fail):
    if state.stack is None:
        fail(f"Calling `box` on empty stack")
    (head, rest) = state.stack
    box, new_state = state.add_box(head)
    return new_state.with_stack((box, rest))


@module.register("-!>")
def read_box_top(state: State, fail: Fail):
    if state.stack is None:
        fail(f"calling `-!>` on empty stack")
    (box, rest) = state.stack

    if box.tag != "box":
        fail(f"{render_value_as_source(box)} is not a box")

    read_value = state.read_box(box.id)
    if read_value is None:
        fail(f"This shouldn't ever happen. Reading a box returned an empty stack.")
    (head, _rest) = read_value
    return state.with_stack((head, rest))


@module.register("->")
def read_box(state: State, fail: Fail):
    if state.stack is None:
        fail(f"calling `->` on empty stack")
    (box, rest) = state.stack

    if box.tag != "box":
        fail(f"{render_value_as_source(box)} is not a box")

    read_value = state.read_box(box.id)
    if read_value is None:
        fail(f"This shouldn't ever happen. Reading a box returned an empty stack.")
    while read_value[1] is not None:  # type: ignore
        (_, read_value) = read_value  # type: ignore
    return state.with_stack((read_value[0], rest))  # type: ignore


@module.register("<-")
def write_to_box(state: State, fail: Fail):
    if state.stack is None or state.stack[1] is None:
        fail(f"calling `<-` on stack too shallow")
    (value, (box, rest)) = state.infinite_stack()

    if box.tag != "box":
        fail(f"{render_value_as_source(box)} is not a box")

    read_value = state.read_box(box.id)
    return state.with_stack(rest).set_box(box.id, (value, read_value[1]))


@module.register("<[")
def begin_transaction(state: State, fail: Fail):
    if state.stack is None:
        fail(f"calling `<[` on empty stack")
    (box, rest) = state.infinite_stack()

    if box.tag != "box":
        fail(f"{render_value_as_source(box)} is not a box")

    read_value = state.read_box(box.id)
    if read_value is None:
        fail(f"This shouldn't ever happen. Reading a box returned an empty stack.")
    (box_head, box_rest) = read_value
    return state.with_stack(rest).set_box(box.id, (box_head, (box_head, box_rest)))


@module.register("]>")
def commit(state: State, fail: Fail):
    if state.stack is None:
        fail(f"calling `]>` on empty stack")
    (box, rest) = state.infinite_stack()

    if box.tag != "box":
        fail(f"{render_value_as_source(box)} is not a box")

    return state.with_stack(rest).commit_box(box.id)


@module.register("<<<")
def rollback(state: State, fail: Fail):
    if state.stack is None:
        fail(f"calling `<<<` on empty stack")
    (box, rest) = state.infinite_stack()

    if box.tag != "box":
        fail(f"{render_value_as_source(box)} is not a box")

    _value, state = state.with_stack(rest).pop_box(box.id)
    return state


@module.register("<<<?")
def rollback_pop(state: State, fail: Fail):
    if state.stack is None:
        fail(f"calling `<<<` on empty stack")
    (box, rest) = state.infinite_stack()

    if box.tag != "box":
        fail(f"{render_value_as_source(box)} is not a box")

    value, state = state.with_stack(rest).pop_box(box.id)
    return state.push(value)


# not to create a circular dependency with prelude
@make_simple("swap")
def __swap(stack: Tuple[Value, Tuple[Value, Stack]], scope: Scope, fail: Fail):
    (y, (x, rest)) = stack
    return (x, (y, rest)), scope


@make_simple("<=-impl")
def __change_box(stack: Tuple[Value, Tuple[Value, Stack]], scope: Scope, fail: Fail):
    """
    {
      :fn var :a-box var
        a-box <[
            a-box -!> fn !
            a-box swap <-
        a-box ]>
    } :<= jar
    """
    (fn, (box, rest)) = stack

    if box.tag != "box":
        fail(f"{render_value_as_source(box)} is not a box")

    if fn.tag != "code" and fn.tag != "native":
        fail(f"{render_value_as_source(fn)} is not a function")

    code = raw_function(
        Put(box), Put(begin_transaction), CallByValue(),
        Put(box), Put(read_box_top), CallByValue(),
        Put(fn), CallByValue(),
        Put(box), Put(__swap), CallByValue(), Put(write_to_box), CallByValue(),
        Put(box), Put(commit), CallByValue(),
        name="<=-impl!",
    )
    return (code, rest), scope


module.add("<=", raw_function(Put(__change_box), CallByValue(), CallByValue(), name="<="))


@module.register("<X-")
def kill_box(state: State, fail: Fail):
    if state.stack is None:
        fail("Calling `<X-` on an empty stack")
    box, rest = state.infinite_stack()

    if box.tag != "box":
        fail(f"Calling `<X-` on {render_value_as_source(box)}")

    return state.kill_box(box.id).with_stack(rest)
