"""
Utilities for creating built-in modules
"""

from dataclasses import field, dataclass
from immutables import Map
from typing import Callable,  NoReturn, Optional, TypeVar, Dict, Tuple
import gurklang.vm_utils as vm_utils
from gurklang.types import Code, CodeFlags, Instruction, Scope, Stack, State, Value, NativeFunction, Vec

Z = TypeVar("Z", bound=Stack, contravariant=True)


def _fail(name: str, reason: str, stack: Stack):
    print("Failure in function", name)
    print("Reason:", reason)
    print("> Stack: ", "[" + " ".join(map(vm_utils.stringify_value, vm_utils.repr_stack(stack))) + "]")
    raise RuntimeError(name, reason)


Fail = Callable[[str], NoReturn]


@dataclass
class Module:
    name: str
    members: Dict[str, Value] = field(init=False)

    def __post_init__(self):
        self.members = {}

    def add(self, member_name: str, value: Value):
        self.members[member_name] = value

    def register_simple(self, name: Optional[str] = None):
        def inner(fn: Callable[[Z, Fail], Stack]) -> NativeFunction:
            native_fn = make_simple(name)(fn)  # type: ignore
            self.add(native_fn.name, native_fn)
            return native_fn
        return inner

    def register(self, name: Optional[str] = None):
        def inner(fn: Callable[[State, Fail], State]) -> NativeFunction:
            native_fn = make_function(name)(fn)  # type: ignore
            self.add(native_fn.name, native_fn)
            return native_fn
        return inner

    def make_scope(self, id: int, parent: Optional[Scope]=None):
        if parent is None:
            return Scope(parent=None, id=id, values=Map(self.members))
        else:
            return Scope(parent=parent.id, id=id, values=Map(self.members))


def make_simple(name: Optional[str] = None):
    def inner(fn: Callable[[Z, Fail], Stack]) -> NativeFunction:
        def new_fn(state: State, fail: Fail):
            stack = fn(state.stack, fail)
            return state.with_stack(stack)
        new_fn.__name__ = fn.__name__
        return make_function(name)(new_fn)
    return inner


def make_function(name: Optional[str] = None):
    def inner(fn: Callable[[State, Fail], State]) -> NativeFunction:
        fn_name = name or fn.__name__.replace("_", "-")
        def new_fn(state: State):
            local_fail: Fail = lambda reason: _fail(fn_name, reason, state.stack)
            try:
                return fn(state, local_fail)
            except Exception as e:
                local_fail(f"uncaught exception {type(e).__name__}: {' '.join(e.args)}")
        native_fn = NativeFunction(new_fn, fn_name)
        return native_fn
    return inner


def raw_function(*instructions: Instruction, name: str = "<raw>", source_code: Optional[str] = None):
    """
    Create `Code` with no closure and flags set to PARENT_SCORE
    """
    return Code(
        instructions,
        closure=None,
        flags=CodeFlags.PARENT_SCOPE,
        name=name,
        source_code=source_code
    )



def vec_to_stack(t: Value, fail: Fail) -> Stack:
    stack = None
    if t.tag != "vec":
        fail(f"expected tuple, got {t}")
    while True:
        if len(t.values) == 0:
            return stack
        if len(t.values) != 2:
            fail(f"got tuple of size {len(t.values)} {vm_utils.stringify_value(t)}, expected 2")
        head, rest = t.values
        if rest.tag != "vec":
            fail(f"expected tuple as second element, got {rest}")
        t = rest
        stack = (head, stack)


def stack_to_vec(stack: Stack) -> Vec:
    rv = Vec([])
    while stack is not None:
        head, stack = stack  # type: ignore
        rv = Vec([head, rv])
    return rv
