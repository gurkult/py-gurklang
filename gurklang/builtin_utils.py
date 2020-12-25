"""
Utilities for creating built-in modules
"""

from dataclasses import field, dataclass
from immutables import Map
from typing import Callable,  NoReturn, Optional, TypeVar, Dict, Tuple
from .vm_utils import repr_stack, stringify_value
from gurklang.types import Code, CodeFlags, Instruction, Scope, Stack, State, Value, NativeFunction

Z = TypeVar("Z", bound=Stack, contravariant=True)


def _fail(name: str, reason: str, stack: Stack, scope: Scope):
    print("Failure in function", name)
    print("Reason:", reason)
    print("> Stack: ", "[" + " ".join(map(stringify_value, repr_stack(stack))) + "]")
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
        def inner(fn: Callable[[Z, Scope, Fail], Tuple[Stack, Scope]]) -> NativeFunction:
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
        return Scope(parent=parent, id=id, values=Map(self.members))


def make_simple(name: Optional[str] = None):
    def inner(fn: Callable[[Z, Scope, Fail], Tuple[Stack, Scope]]) -> NativeFunction:
        def new_fn(state: State, fail: Fail):
            stack, scope = fn(state.stack, state.scope, fail)
            return state.with_stack(stack).with_scope(scope)
        new_fn.__name__ = fn.__name__
        return make_function(name)(new_fn)
    return inner


def make_function(name: Optional[str] = None):
    def inner(fn: Callable[[State, Fail], State]) -> NativeFunction:
        fn_name = name or fn.__name__.replace("_", "-")
        def new_fn(state: State):
            stack, scope = state.stack, state.scope
            local_fail: Fail = lambda reason: _fail(fn_name, reason, stack, scope)
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

R"""saybegin
!gurklang

:math ( + ) import

1 :x var
x println

{ x 1 + :x var } parent-scope :x++ jar

x++
x println

x++ x++
x println
sayend"""