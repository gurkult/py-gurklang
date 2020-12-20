from immutables import Map
from typing import Any, Callable, Iterator, NoReturn, Optional, TypeVar
from .vm_utils import repr_stack, stringify_value
from . import builtin_values
from gurklang.types import (
    Scope, Stack,

    Instruction,
    Put, Call,

    Value,
    Atom, Int, Str, Code, NativeFunction, Vec,
)


_SCOPE_ID = 0
def generate_scope_id():
    global _SCOPE_ID
    _SCOPE_ID += 1
    return _SCOPE_ID


def make_scope(parent: Optional[Scope]) -> Scope:
    return Scope(parent, generate_scope_id(), Map())


def call(stack: Stack, scope: Scope, function: Value) -> tuple[Stack, Scope]:
    if function.tag == "native":
        return function.fn(stack, scope)

    elif function.tag == "code":
        local_scope = make_scope(parent=scope.join_closure_scope(function.closure))

        for instruction in function.instructions:
            stack, local_scope = execute(stack, local_scope, instruction)

        assert local_scope.parent is not None
        return stack, local_scope.parent

    else:
        raise RuntimeError(function)


def execute(stack: Stack, scope: Scope, instruction: Instruction) -> tuple[Stack, Scope]:
    if instruction.tag == "put":
        return (instruction.value, stack), scope

    elif instruction.tag == "put_code":
        return (Code(instruction.value, scope), stack), scope

    elif instruction.tag == "call":
        return call(stack, scope, scope[instruction.function_name])

    elif instruction.tag == "make_vec":
        elements = []
        for _ in range(instruction.size):
            head, stack = stack  # type: ignore
            elements.append(head)
        return (Vec(elements[::-1]), stack), scope

    else:
        raise RuntimeError(instruction)


def make_builtins(scope_id: int):
    return Scope(parent=None, id=scope_id, values=builtin_values.module_map)


builtin_scope = make_builtins(generate_scope_id())
global_scope = make_scope(parent=builtin_scope)


def run(instructions):
    return call(
        stack=None,
        scope=global_scope,
        function=Code(instructions, closure=None)
    )
