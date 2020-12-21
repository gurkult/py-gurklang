from dataclasses import dataclass
from immutables import Map
from typing import Optional, Union
from . import builtin_values
from gurklang.types import CodeFlags, MakeScope, NativeFunction, PopScope, Scope, Stack, Instruction, Value, Code, Vec
from collections import deque


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
        instructions: "deque[Instruction]" = deque()

        def load_function(function: Code):
            if function.flags & CodeFlags.PARENT_SCOPE:
                instructions.extendleft(reversed(function.instructions))
            else:
                instructions.appendleft(PopScope())
                instructions.extendleft(reversed(function.instructions))
                instructions.appendleft(MakeScope(parent=scope.join_closure_scope(function.closure)))


        load_function(function)

        while instructions:
            instruction = instructions.popleft()
            # print("instruction", instruction)
            r = execute(stack, scope, instruction)
            if isinstance(r, Done):
                stack, scope = r.stack, r.scope
            elif isinstance(r.function, NativeFunction):
                stack, scope = r.function.fn(stack, scope)
            else:
                load_function(r.function)

        return stack, scope
    else:
        raise RuntimeError(function)

@dataclass
class Done:
    stack: Stack
    scope: Scope

@dataclass
class Recur:
    function: Union[NativeFunction, Code]


def execute(stack: Stack, scope: Scope, instruction: Instruction) -> Union[Done, Recur]:
    if instruction.tag == "put":
        return Done((instruction.value, stack), scope)

    elif instruction.tag == "put_code":
        return Done((Code(instruction.value, scope), stack), scope)

    elif instruction.tag == "call":
        function = scope[instruction.function_name]
        if function.tag != "code" and function.tag != "native":
            raise RuntimeError(function)
        return Recur(function)

    elif instruction.tag == "make_vec":
        elements = []
        for _ in range(instruction.size):
            head, stack = stack  # type: ignore
            elements.append(head)
        return Done((Vec(elements[::-1]), stack), scope)

    elif instruction.tag == "make_scope":
        return Done(stack, make_scope(instruction.parent))

    elif instruction.tag == "pop_scope":
        return Done(stack, scope.parent)  # type: ignore

    else:
        raise RuntimeError(instruction)


builtin_scope = builtin_values.module.make_scope(generate_scope_id())
global_scope = make_scope(parent=builtin_scope)


def run(instructions):
    return call(
        stack=None,
        scope=global_scope,
        function=Code(instructions, closure=None)
    )
