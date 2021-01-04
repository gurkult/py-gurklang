from typing import List, TypeVar, Tuple
from ..builtin_utils import BuiltinModule, Fail, make_simple, vec_to_stack, stack_to_vec
from ..types import CallByValue, Code, CodeFlags, Instruction, Put, Value, Stack, Scope


module = BuiltinModule("coro")
T, V, S = Tuple, Value, Stack
Z = TypeVar("Z", bound=Stack)


@make_simple()
def __iterate(stack: T[V, T[V, S]], fail: Fail):
    (initial, (fn, rest)) = stack
    initial_stack_vec = vec_to_stack(initial, fail)

    @make_simple()
    def __set_resulting_stack(resulting_stack: Stack, _: Fail):
        stack_vec = stack_to_vec(resulting_stack)
        return (stack_vec, (fn, rest))

    instructions: List[Instruction] = [
        Put(restore_stack((fn, initial_stack_vec))),    # stack: restore_stack(...)
        CallByValue(),                                  # stack: (fn, (initial_stack_vec, None))
        CallByValue(),                                  # stack: resulting stack
        Put(__set_resulting_stack),                     # stack: (__set_resulting_stack)
        CallByValue()                                   # stack: (resulting Vec, (fn, rest))
    ]
    code = Code(instructions, closure=None, flags=CodeFlags.PARENT_SCOPE, name="--iterate")
    return (code, rest)


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
    def __restore_stack(__stack: Stack, __fail: Fail):
        return stack
    return __restore_stack
