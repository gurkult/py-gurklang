from immutables import Map
from typing import Callable, Dict, Optional, Sequence, Union, Tuple
from . import prelude
from gurklang.types import (
    CallByValue, CodeFlags, MakeScope, NativeFunction, PopScope, Put,
    Scope, Stack, Instruction, Code, State, Value, Vec
)
from collections import deque
import threading


MiddlewareT = Callable[[Instruction, Stack, Stack], None]


_SCOPE_ID_LOCK = threading.Lock()
_SCOPE_ID = 0
def generate_scope_id():
    global _SCOPE_ID
    with _SCOPE_ID_LOCK:
        _SCOPE_ID += 1
    return _SCOPE_ID


def make_scope(parent: Optional[int]) -> Scope:
    return Scope(parent, generate_scope_id(), Map())


def _load_function(pipe: "deque[Instruction]", function: Union[Code, NativeFunction]):
    if function.tag == "native":
        pipe.append(CallByValue())
        pipe.append(Put(function))
    elif function.flags & CodeFlags.PARENT_SCOPE or function.closure is None:
        pipe.extend(reversed(function.instructions))
    else:
        pipe.append(PopScope())
        pipe.extend(reversed(function.instructions))
        pipe.append(MakeScope(function.closure))


def call(state: State, function: Union[Code, NativeFunction]) -> State:
    """
    Stackless implementation of calling a function.

    Instructions are piped into a deque, from which they're popped
    and executed one by one.
    """
    return call_with_middleware(state, function, lambda _, __, ___: None)


def call_with_middleware(
    state: State,
    function: Union[Code, NativeFunction],
    middleware: MiddlewareT,
) -> State:
    """
    Like `call`, but execute some action on each change
    """
    pipe: "deque[Instruction]" = deque()

    _load_function(pipe, function)

    while pipe:
        instruction = pipe.pop()

        old_state = state

        if instruction.tag == "call":
            pipe.append(CallByValue())
            pipe.append(Put(state.look_up_name_in_current_scope(instruction.function_name)))

        elif instruction.tag == "call_by_value":
            (function, stack) = state.stack  # type: ignore
            state = state.with_stack(stack)
            if function.tag == "code":
                _load_function(pipe, function)
            else:
                state = function.fn(state)

        else:
            state = execute(state, instruction)

        middleware(instruction, old_state.stack, state.stack)

    return state


def execute(state: State, instruction: Instruction) -> State:
    """
    Execute an instruction and return new state of the system.
    """
    if instruction.tag == "put":
        return state.push(instruction.value)

    elif instruction.tag == "put_code":
        return state.push(
            Code(
                instructions=instruction.instructions,
                closure=state.current_scope_id,
                source_code=instruction.source_code,
            )
        )

    elif instruction.tag == "make_vec":
        stack = state.stack
        elements = []
        for _ in range(instruction.size):
            head, stack = stack  # type: ignore
            elements.append(head)
        return state.with_stack(stack).push(Vec(elements[::-1]))

    elif instruction.tag == "make_scope":
        return state.make_scope(instruction.parent_id, generate_scope_id())

    elif instruction.tag == "pop_scope":
        return state.pop_scope()

    else:
        raise RuntimeError(instruction)


builtin_scope = prelude.module.make_scope(generate_scope_id())
global_scope = make_scope(parent=builtin_scope.id)


def run(instructions: Sequence[Instruction]):
    return run_with_middleware(instructions, middleware = lambda _, __, ___: None)


def run_with_middleware(instructions: Sequence[Instruction], middleware: MiddlewareT):
    return call_with_middleware(
        State(
            None,
            Map({builtin_scope.id: builtin_scope, global_scope.id: global_scope}),
            (global_scope.id, (builtin_scope.id, None)),
            Map(),
            Map(),
            0
        ),
        Code(instructions, closure=None, name="<entry-point>"),
        middleware
    )
