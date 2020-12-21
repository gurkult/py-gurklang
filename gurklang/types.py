from __future__ import annotations
from enum import  IntFlag
from immutables import Map
from typing import Callable, ClassVar, Mapping, Sequence, Union, Literal, Optional
from dataclasses import dataclass


@dataclass(frozen=True, repr=False)
class Scope:
    parent: Optional[Scope]
    id: int
    values: Map

    def __getitem__(self, name: str) -> Value:
        scope = self
        while scope is not None:
            if name in scope.values:
                return scope.values[name]
            scope = scope.parent
        raise KeyError(name)

    def __repr__(self):
        return f"Map(values={set(self.values.keys())}, id={self.id!r}, parent={self.parent!r})"

    def with_member(self, key: str, value: Value) -> Scope:
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
class CallByName:
    # Call a function by name
    function_name: str
    tag: ClassVar[Literal["call"]] = "call"

@dataclass(frozen=True)
class CallByValue:
    # Call a function by value
    tag: ClassVar[Literal["call_by_value"]] = "call_by_value"

@dataclass(frozen=True)
class MakeVec:
    # Collect `size` elements and make a vec
    size: int
    tag: ClassVar[Literal["make_vec"]] = "make_vec"

@dataclass(frozen=True)
class MakeScope:
    parent: Optional[Scope]
    tag: ClassVar[Literal["make_scope"]] = "make_scope"

@dataclass(frozen=True)
class PopScope:
    tag: ClassVar[Literal["pop_scope"]] = "pop_scope"

# `Instruction` is a single step executed by the interpreter
Instruction = Union[Put, PutCode, CallByName, CallByValue, MakeVec, MakeScope, PopScope]


class CodeFlags(IntFlag):
    EMPTY = 0
    PARENT_SCOPE = 1


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
    flags: CodeFlags = CodeFlags.EMPTY
    tag: ClassVar[Literal["code"]] = "code"

@dataclass
class NativeFunction:
    # A function implemented in Python, like `if` or `vec`
    fn: Callable[[Stack, Scope], Union[tuple[Stack, Scope], Recur]]
    tag: ClassVar[Literal["native"]] = "native"

Value = Union[Atom, Str, Int, Vec, Code, NativeFunction]


@dataclass
class Recur:
    stack: Stack
    scope: Scope
    function: Union[NativeFunction, Code]
