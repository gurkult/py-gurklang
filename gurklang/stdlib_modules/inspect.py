import pprint
import math

from typing import Sequence, TypeVar, Tuple
from ..vm_utils import stringify_value
from ..builtin_utils import Module, Fail
from ..types import Atom, Code, Instruction, Value, Stack, Scope, Int, Vec

from collections import deque


module = Module("inspect")
T, V, S = Tuple, Value, Stack
Z = TypeVar("Z", bound=Stack)


@module.register_simple()
def code_dump(stack: T[V, S], scope: Scope, fail: Fail):
    (code, rest) = stack
    if code.tag != "code":
        fail(f"{code} is not code")
    pprint.pprint(code.instructions)
    return rest, scope


@module.register_simple()
def dis(stack: T[V, S], scope: Scope, fail: Fail):
    (head, rest) = stack

    if head.tag == "atom":
        head = scope[head.value]

    if head.tag != "code":
        fail(f"{head} is not valid code or atom")

    last_id = 1

    tasks: "deque[tuple[int, Sequence[Instruction]]]" = deque([(last_id, head.instructions)])
    seen_code = {id(head.instructions): last_id}

    def get_code_id(instructions: Sequence[Instruction]):
        nonlocal last_id
        old_id = seen_code.get(id(instructions))
        if old_id is not None:
            return old_id
        last_id += 1
        tasks.append((last_id, instructions))
        return last_id

    while tasks:
        uid, instructions = tasks.popleft()
        seen_code[id(instructions)] = last_id
        print(f"Disassembling function {uid}:")

        for instruction in instructions:
            if instruction.tag == "put":
                if instruction.value.tag == "code":
                    code_id = get_code_id(instruction.value.instructions)  # type: ignore
                    print(f"Put (code {code_id})")
                else:
                    print(f"Put {instruction.value}")

            elif instruction.tag == "call":
                print(f"Call {instruction.function_name}")

            elif instruction.tag == "call_by_value":
                print("CallByValue (some code)")

            elif instruction.tag == "put_code":
                code_id = get_code_id(instruction.value)
                print(f"PutCode (code #{code_id})")

            elif instruction.tag == "make_vec":
                print(f"MakeVec of size {instruction.size}")

            elif instruction.tag == "make_scope":
                if instruction.parent is None:
                    print("MakeScope with no parent")
                else:
                    print(f"MakeScope from closure with keys: {' '.join(instruction.parent.values.keys())}")

            elif instruction.tag == "pop_scope":
                print("PopScope")
        print()

    return rest, scope



@module.register_simple("type")
def get_type(stack: T[V, S], scope: Scope, fail: Fail):
    (head, rest) = stack
    return (Atom(head.tag), rest), scope
