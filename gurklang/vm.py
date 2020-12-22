from immutables import Map
from typing import Optional, Union, Tuple
from . import builtin_values
from gurklang.types import CallByValue, CodeFlags, MakeScope, NativeFunction, PopScope, Put, Scope, Stack, Instruction, Value, Code, Vec, Recur
from collections import deque


_SCOPE_ID = 0
def generate_scope_id():
    global _SCOPE_ID
    _SCOPE_ID += 1
    return _SCOPE_ID


def make_scope(parent: Optional[Scope]) -> Scope:
    return Scope(parent, generate_scope_id(), Map())


def call(stack: Stack, scope: Scope, function: Value) -> Tuple[Stack, Scope]:
    if function.tag == "code" or function.tag == "native":
        instructions: "deque[Instruction]" = deque()

        def load_function(function: Union[Code, NativeFunction]):
            if function.tag == "native":
                instructions.appendleft(CallByValue())
                instructions.appendleft(Put(function))
            elif function.flags & CodeFlags.PARENT_SCOPE:
                instructions.extendleft(reversed(function.instructions))
            else:
                instructions.appendleft(PopScope())
                instructions.extendleft(reversed(function.instructions))
                instructions.appendleft(MakeScope(parent=scope.join_closure_scope(function.closure)))

        load_function(function)

        while instructions:
            instruction = instructions.popleft()
            r = execute(stack, scope, instruction)
            if isinstance(r, tuple):
                stack, scope = r
            else:
                stack, scope = r.stack, r.scope
                if isinstance(r.function, NativeFunction):
                    v = r.function.fn(stack, scope)
                    if type(v) is Recur:
                        stack, scope = v.stack, v.scope  # type: ignore
                        instructions.appendleft(CallByValue())
                        instructions.appendleft(Put(v.function))  # type: ignore
                    else:
                        stack, scope = v  # type: ignore
                else:
                    load_function(r.function)
        return stack, scope
    else:
        raise RuntimeError(function)


def execute(stack: Stack, scope: Scope, instruction: Instruction) -> Union[Tuple[Stack, Scope], Recur]:
    if instruction.tag == "put":
        return (instruction.value, stack), scope

    elif instruction.tag == "put_code":
        return (Code(instruction.value, scope), stack), scope

    elif instruction.tag == "call":
        function = scope[instruction.function_name]
        if function.tag not in ["code", "native"]:
            raise RuntimeError(function)
        return Recur(stack, scope, function)  # type: ignore

    elif instruction.tag == "call_by_value":
        if stack is None:
            raise RuntimeError("CallByValue on empty stack")
        (function, rest) = stack
        if function.tag not in ["code", "native"]:
            raise RuntimeError(function)
        return Recur(rest, scope, function)  # type: ignore

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


builtin_scope = builtin_values.module.make_scope(generate_scope_id())
global_scope = make_scope(parent=builtin_scope)


def run(instructions):
    return call(
        stack=None,
        scope=global_scope,
        function=Code(instructions, closure=None)
    )
