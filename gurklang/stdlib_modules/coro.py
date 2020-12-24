from typing import List, Sequence, TypeVar, Tuple
from ..vm_utils import stringify_value
from ..builtin_utils import Module, Fail, make_simple
from ..types import Atom, CallByValue, Code, CodeFlags, Instruction, Put, Value, Stack, Scope, Int, Vec


module = Module("coro")
T, V, S = Tuple, Value, Stack
Z = TypeVar("Z", bound=Stack)


def _vec_to_stack(t: Value, fail: Fail) -> Stack:
    stack = None
    if t.tag != "vec":
        fail(f"expected tuple, got {t}")
    while True:
        if len(t.values) == 0:
            return stack
        if len(t.values) != 2:
            fail(f"got tuple of size {len(t.values)} {stringify_value(t)}, expected 2")
        head, rest = t.values
        if rest.tag != "vec":
            fail(f"expected tuple as second element, got {rest}")
        t = rest
        stack = (head, stack)


def _stack_to_vec(stack: Stack) -> Vec:
    rv = Vec([])
    while stack is not None:
        head, stack = stack  # type: ignore
        rv = Vec([head, rv])
    return rv


@make_simple()
def __iterate(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (initial, (fn, rest)) = stack
    initial_stack_vec = _vec_to_stack(initial, fail)

    @make_simple()
    def __set_resulting_stack(resulting_stack: Stack, resulting_scope: Scope, _: Fail):
        stack_vec = _stack_to_vec(resulting_stack)
        return (stack_vec, (fn, rest)), resulting_scope

    instructions: List[Instruction] = [
        Put(restore_stack((fn, initial_stack_vec))),    # stack: restore_stack(...)
        CallByValue(),                                  # stack: (fn, (initial_stack_vec, None))
        CallByValue(),                                  # stack: resulting stack
        Put(__set_resulting_stack),                     # stack: (__set_resulting_stack)
        CallByValue()                                   # stack: (resulting Vec, (fn, rest))
    ]
    code = Code(instructions, closure=None, flags=CodeFlags.PARENT_SCOPE, name="--iterate")
    return (code, rest), scope


module.add("iterate",
    Code(
        [Put(__iterate), CallByValue(), CallByValue()],
        closure=None,
        flags=CodeFlags.PARENT_SCOPE,
        name="--iterate",
    )
)


def restore_stack(stack: Stack):
    @make_simple()
    def __restore_stack(__stack: Stack, scope: Scope, fail: Fail):
        return stack, scope
    return __restore_stack
