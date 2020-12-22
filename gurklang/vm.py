from immutables import Map
from typing import Optional, Union, Tuple
from . import prelude
from gurklang.types import (
    CallByValue, CodeFlags, MakeScope, NativeFunction, PopScope, Put,
    Scope, Stack, Instruction, Code, Vec
)
from collections import deque


_SCOPE_ID = 0
def generate_scope_id():
    global _SCOPE_ID
    _SCOPE_ID += 1
    return _SCOPE_ID


def make_scope(parent: Optional[Scope]) -> Scope:
    return Scope(parent, generate_scope_id(), Map())


def _load_function(scope: Scope, pipe: "deque[Instruction]", function: Union[Code, NativeFunction]):
    if function.tag == "native":
        pipe.append(CallByValue())
        pipe.append(Put(function))
    elif function.flags & CodeFlags.PARENT_SCOPE:
        pipe.extend(reversed(function.instructions))
    else:
        pipe.append(PopScope())
        pipe.extend(reversed(function.instructions))
        pipe.append(MakeScope(scope.join_closure_scope(function.closure)))


def call(stack: Stack, scope: Scope, function: Union[Code, NativeFunction]) -> Tuple[Stack, Scope]:
    """
    Stackless implementation of calling a function.

    Instructions are piped into a deque, from which they're popped
    and executed one by one.
    """
    pipe: "deque[Instruction]" = deque()

    _load_function(scope, pipe, function)

    while pipe:
        instruction = pipe.pop()

        if instruction.tag == "call":
            pipe.append(CallByValue())
            pipe.append(Put(scope[instruction.function_name]))
        elif instruction.tag == "call_by_value":
            (function, stack) = stack  # type: ignore
            if function.tag == "code":
                _load_function(scope, pipe, function)
            else:
                stack, scope = function.fn(stack, scope)
        else:
            stack, scope = execute(stack, scope, instruction)

    return stack, scope


def execute(stack: Stack, scope: Scope, instruction: Instruction) -> Tuple[Stack, Scope]:
    """
    Execute an instruction and return new state of the system.

    Pure function, i.e. doesn't perform any side effects.
    """
    if instruction.tag == "put":
        return (instruction.value, stack), scope

    elif instruction.tag == "put_code":
        return (Code(instruction.value, scope), stack), scope

    elif instruction.tag == "make_vec":
        elements = []
        for _ in range(instruction.size):
            head, stack = stack  # type: ignore
            elements.append(head)
        return (Vec(elements[::-1]), stack), scope

    elif instruction.tag == "make_scope":
        return stack, make_scope(instruction.parent)

    elif instruction.tag == "pop_scope":
        return stack, scope.parent  # type: ignore

    else:
        raise RuntimeError(instruction)


builtin_scope = prelude.module.make_scope(generate_scope_id())
global_scope = make_scope(parent=builtin_scope)


def run(instructions):
    return call(
        stack=None,
        scope=global_scope,
        function=Code(instructions, closure=None)
    )
