from __future__ import annotations
from enum import  IntFlag
from immutables import Map
try:
    from typing_extensions import Literal
except ImportError:
    from typing import Literal
from typing import Callable, ClassVar, Dict, Mapping, Sequence, Union, Optional, Tuple
from dataclasses import dataclass, field, replace as dataclass_replace


@dataclass(frozen=True, repr=False)
class Scope:
    parent: Optional[Scope]
    id: int
    values: Map
    _cache: Dict[str, Value] = field(default_factory=dict)

    def __getitem__(self, name: str) -> Value:
        cache = self._cache
        if name in cache:
            return cache[name]
        while self is not None:
            v = self._cache.get(name) or self.values.get(name)
            if v is not None:
                cache[name] = v
                return v
            self = self.parent
        raise KeyError(name) from None

    def __repr__(self):
        return f"<Scope {self.id!r}: {' '.join(self.values.keys())}, id=, parent={self.parent!r}>"

    def without_member(self, key: str, value: Value):
        if key not in self.values:
            return self
        return Scope(self.parent, self.id, self.values.delete(key))

    def with_member(self, key: str, value: Value) -> Scope:
        if key in self.values:
            raise RuntimeError(f"Trying to reassign {key}")
        return Scope(self.parent, self.id, self.values.set(key, value))

    def with_members(self, update: Mapping[str, Value]):
        return Scope(self.parent, self.id, self.values.update(update))

    def with_parent(self, parent: Optional[Scope]):
        return Scope(parent, self.id, self.values)

    def join_closure_scope(self, closure_scope: Optional[Scope]) -> Scope:
        """
        Refresh a closure scope that has `self` somewhere upstream.
        This is needed because scopes are immutable, and an outer scope
        might've been updated with new names or names being redefined.
        """
        if closure_scope is None or self.id == closure_scope.id:
            return self
        else:
            return closure_scope.with_parent(self.join_closure_scope(closure_scope.parent))


# The stack is immutable and is modelled as a linked list:
Stack = Optional[Tuple["Value", "Stack"]]


@dataclass(frozen=True)
class State:
    stack: Stack
    scope: Scope
    boxes: Map

    def add(self, *values: "Value"):
        stack = self.stack
        for value in values:
            stack = (value, stack)
        return self.with_stack(stack)

    def box_value(self, id: int) -> Optional["Value"]:
        return self.boxes.get(id)

    def set_box(self, id: int, value: Value):
        return self.with_boxes(self.boxes.set(id, value))

    def with_stack(self, stack: Stack):
        return dataclass_replace(self, stack=stack)

    def with_scope(self, scope: Scope):
        return dataclass_replace(self, scope=scope)

    def with_boxes(self, boxes: Map):
        return dataclass_replace(self, boxes=boxes)


@dataclass(frozen=True)
class Put:
    """Put a single value on top of the stack"""
    value: Value
    tag: ClassVar[Literal["put"]] = "put"

@dataclass(frozen=True)
class PutCode:
    """Create a closure and put a code value on top of the stack"""
    value: Sequence[Instruction]
    source_code: Optional[str] = None
    tag: ClassVar[Literal["put_code"]] = "put_code"

@dataclass(frozen=True)
class CallByName:
    """Call a function by name"""
    function_name: str
    tag: ClassVar[Literal["call"]] = "call"

@dataclass(frozen=True)
class CallByValue:
    """Pop a function from the top of the stack and call it"""
    tag: ClassVar[Literal["call_by_value"]] = "call_by_value"

@dataclass(frozen=True)
class MakeVec:
    """Collect `size` elements and make a tuple"""
    size: int
    tag: ClassVar[Literal["make_vec"]] = "make_vec"

@dataclass(frozen=True)
class MakeScope:
    """Create a local scope given a parent scope"""
    parent: Optional[Scope]
    tag: ClassVar[Literal["make_scope"]] = "make_scope"

@dataclass(frozen=True)
class PopScope:
    """Discard the topmost scope and return to the parent scope"""
    tag: ClassVar[Literal["pop_scope"]] = "pop_scope"

# `Instruction` is a single step executed by the interpreter
Instruction = Union[Put, PutCode, CallByName, CallByValue, MakeVec, MakeScope, PopScope]


class CodeFlags(IntFlag):
    """Optimization flags used by `Code`"""
    EMPTY = 0
    PARENT_SCOPE = 1


_atom_cache: Dict[str, Atom] = {}

@dataclass(eq=False)
class Atom:
    """
    Atom, like :true

    Atoms are cached and compared by identity.
    """
    value: str
    _original: bool = False
    tag: ClassVar[Literal["atom"]] = "atom"

    def __post_init__(self):
        if not self._original:
            raise RuntimeError(f"Atoms must be acquired via the `Atom.make` method")

    @staticmethod
    def make(name: str) -> Atom:
        if name not in _atom_cache:
            _atom_cache[name] = Atom(name, True)
        return _atom_cache[name]

    @staticmethod
    def bool(x: bool) -> Atom:
        return Atom.make("true" if x else "false")


@dataclass(frozen=True)
class Str:
    """String, like 'hello'"""
    value: str
    tag: ClassVar[Literal["str"]] = "str"

@dataclass(frozen=True)
class Int:
    """Integer, like 42"""
    value: int
    tag: ClassVar[Literal["int"]] = "int"

@dataclass(frozen=True)
class Vec:
    """
    Vector (tuple), like (a b 7)

    Tuples are referred to as vectors to prevent collisions with `Tuple`
    """
    values: Sequence[Value]
    tag: ClassVar[Literal["vec"]] = "vec"

@dataclass(frozen=True)
class Code:
    """Code value like { :b var :a var b a }"""
    instructions: Sequence[Instruction]
    closure: Optional[Scope]
    flags: CodeFlags = CodeFlags.EMPTY
    name: str = "λ"
    source_code: Optional[str] = None
    tag: ClassVar[Literal["code"]] = "code"

    def with_name(self, name: str) -> Code:
        return dataclass_replace(self, name=name)

@dataclass(frozen=True)
class NativeFunction:
    """A function implemented in Python, like `if` or `+`"""
    fn: Callable[[State], State]
    name: str = "λ"
    tag: ClassVar[Literal["native"]] = "native"

@dataclass(frozen=True, eq=False)
class Box:
    id: int
    on_destruction: Callable[[Box], None]
    tag: ClassVar[Literal["box"]] = "box"

    def __eq__(self, other):
        if not isinstance(other, Box):
            return NotImplemented
        return self.id == other.id

    def __del__(self):
        self.on_destruction(self)

Value = Union[Atom, Str, Int, Vec, Code, NativeFunction, Box]
