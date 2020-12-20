from __future__ import annotations
from immutables import Map
from typing import Callable, ClassVar, Sequence, Union, Literal, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class Scope:
    parent: Optional[Scope]
    id: int
    values: Map

    def __getitem__(self, name: str) -> Value:
        if name in self.values:
            return self.values[name]
        elif self.parent is not None:
            return self.parent[name]
        else:
            raise KeyError(name)

    def with_member(self, key: str, value: Value) -> Scope:
        return Scope(self.parent, self.id, self.values.set(key, value))

    def with_parent(self, parent: Optional[Scope]):
        return Scope(parent, self.id, self.values)

    def join_closure_scope(self, closure_scope: Optional[Scope]) -> Scope:
        """
        Refresh a closure scope that has `self` somewhere upstream.
        This is needed because scopes are immutable, and an outer scope
        might've been updated with new names or names being redefined.
        """
        if closure_scope is None:
            return self
        elif self.id == closure_scope.id:
            return self
        else:
            return closure_scope.with_parent(self.join_closure_scope(closure_scope.parent))


# The stack is immutable and is modelled as a linked list:
Stack = Optional[tuple["Value", "Stack"]]


@dataclass(frozen=True)
class Put:
    # Put a single value on top of the stack
    value: Value
    tag: ClassVar[Literal["put"]] = "put"

@dataclass(frozen=True)
class PutCode:
    # Create a closure and put a code value on top of the stack
    value: Sequence[Instruction]
    tag: ClassVar[Literal["put_code"]] = "put_code"

@dataclass(frozen=True)
class Call:
    # Call a function by name
    function_name: str
    tag: ClassVar[Literal["call"]] = "call"

@dataclass(frozen=True)
class MakeVec:
    # Collect `size` elements and make a vec
    size: int
    tag: ClassVar[Literal["make_vec"]] = "make_vec"

# `Instruction` is a single step executed by the interpreter
Instruction = Union[Put, PutCode, Call, MakeVec]


@dataclass
class Atom:
    # Atom, like :true
    value: str
    tag: ClassVar[Literal["atom"]] = "atom"

@dataclass
class Str:
    # String, like "hello"
    value: str
    tag: ClassVar[Literal["str"]] = "str"

@dataclass
class Int:
    # Integer, like 42
    value: int
    tag: ClassVar[Literal["int"]] = "int"

@dataclass
class Vec:
    # Vector (tuple), like (a b 7)
    values: Sequence[Value]
    tag: ClassVar[Literal["vec"]] = "vec"

@dataclass
class Code:
    # Code (funciton), like { :b var :a var b a }
    instructions: Sequence[Instruction]
    closure: Optional[Scope]
    tag: ClassVar[Literal["code"]] = "code"

@dataclass
class NativeFunction:
    # A function implemented in Python, like `if` or `vec`
    fn: Callable[[Stack, Scope], tuple[Stack, Scope]]
    tag: ClassVar[Literal["native"]] = "native"

Value = Union[Atom, Str, Int, Vec, Code, NativeFunction]