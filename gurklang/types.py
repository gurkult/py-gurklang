from __future__ import annotations
from immutables import Map
from typing import Callable, Sequence, Union, Literal, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class Scope:
    parent: Optional[Scope]
    id: int
    values: Map


# The stack is immutable and is modelled as a linked list:
Stack = Optional[tuple["Value", "Stack"]]


@dataclass
class Put:
    # Put a single value on top of the stack
    value: Value
    tag: Literal["put"] = "put"

@dataclass
class PutCode:
    # Create a closure and put a code value on top of the stack
    value: Sequence[Instruction]
    tag: Literal["put_code"] = "put_code"

@dataclass
class Call:
    # Call a function by name
    function_name: str
    tag: Literal["call"] = "call"

# `Instruction` is a single step executed by the interpreter
Instruction = Union[Put, PutCode, Call]


@dataclass
class Atom:
    # Atom, like :true
    value: str
    tag: Literal["atom"] = "atom"

@dataclass
class Str:
    # String, like "hello"
    value: str
    tag: Literal["str"] = "str"

@dataclass
class Int:
    # Integer, like 42
    value: int
    tag: Literal["int"] = "int"

@dataclass
class Vec:
    # Vector (tuple), like (a b 7)
    values: Sequence[Value]
    tag: Literal["vec"] = "vec"

@dataclass
class Code:
    # Code (funciton), like { :b var :a var b a }
    instructions: Sequence[Instruction]
    closure: Optional[Scope]
    tag: Literal["code"] = "code"

@dataclass
class NativeFunction:
    # A function implemented in Python, like `if` or `vec`
    fn: Callable[[Stack, Scope], tuple[Stack, Scope]]
    tag: Literal["native"] = "native"

Value = Union[Atom, Str, Int, Vec, Code, NativeFunction]