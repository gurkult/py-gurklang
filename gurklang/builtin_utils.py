"""
Utilities for creating built-in modules
"""

from dataclasses import field, dataclass
from immutables import Map
from typing import Callable,  NoReturn, Optional, TypeVar, Dict, Tuple
from .vm_utils import repr_stack
from gurklang.types import Scope, Stack, Value, NativeFunction

Z = TypeVar("Z", bound=Stack, contravariant=True)


def _fail(name: str, reason: str, stack: Stack, scope: Scope):
    print(f"Failure in function {name!r}.")
    print("Reason:", reason)
    print("> Stack: ", repr_stack(stack))
    print("> Most inner scope: ", scope.values)
    if scope.parent is not None:
        print("> Parent scope: ", scope.parent.values)
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

    def register(self, name: Optional[str] = None):
        # Z is contravariant because a function should accept a subset of
        # stacks (e.g. only stacks with at least 2 elements)
        def inner(fn: Callable[[Z, Scope, Fail], Tuple[Stack, Scope]]):
            fn_name = name or fn.__name__.replace("_", "-")
            def new_fn(stack, scope):
                local_fail: Fail = lambda reason: _fail(fn_name, reason, stack, scope)
                try:
                    return fn(stack, scope, local_fail)
                except Exception as e:
                    local_fail(f"uncaught exception {type(e)}: {' '.join(e.args)}")
            new_fn.__qualname__ = "new_fn"
            self.add(fn_name, NativeFunction(new_fn))
        return inner

    def make_scope(self, id: int, parent: Optional[Scope]=None):
        return Scope(parent=parent, id=id, values=Map(self.members))
