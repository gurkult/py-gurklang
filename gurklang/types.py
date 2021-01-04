from __future__ import annotations
from enum import  IntFlag
import weakref
from immutables import Map
try:
    from typing_extensions import Literal
except ImportError:
    from typing import Literal
from typing import Any, Callable, ClassVar, Dict, Mapping, Sequence, Union, Optional, Tuple
from dataclasses import dataclass, field, replace as dataclass_replace


@dataclass(frozen=True, repr=False)
class Scope:
    parent: Optional[int]
    id: int
    values: Map

    def get(self, name: str, state: "State") -> Value:
        if name in self.values:
            return self.values[name]
        if self.parent is None:
            raise KeyError(name)
        return state.get_by_name(self.parent, name)

    def __repr__(self):
        return f"<Scope {self.id!r}: parent={self.parent!r}>"

    def without_member(self, key: str):
        return Scope(self.parent, self.id, self.values.delete(key))

    def with_member(self, key: str, value: Value) -> Scope:
        if key in self.values:
            raise RuntimeError(f"Trying to reassign {key}")
        return Scope(self.parent, self.id, self.values.set(key, value))

    def with_members(self, update: Mapping[str, Value]):
        return Scope(self.parent, self.id, self.values.update(update))

    def with_parent(self, parent: Optional[int]):
        return Scope(parent, self.id, self.values)


# The stack is immutable and is modelled as a linked list:
ScopeStack = Optional[Tuple[int, "ScopeStack"]]
Stack = Optional[Tuple["Value", "Stack"]]
InfiniteStack = Tuple["Value",
                Tuple["Value",
                Tuple["Value",
                Tuple["Value",
                Tuple["Value",
                Tuple["Value",
                Tuple["Value",
                Tuple["Value", "InfiniteStack"]]]]]]]]


@dataclass(frozen=True)
class State:
    stack: Stack
    scopes: Map  # Map[int, Scope]
    scope_stack: ScopeStack
    boxes: Map  # Map[int, Stack]
    box_in_transaction: Map  # Map[int, bool]
    last_box_id: int

    @staticmethod
    def make(global_scope: Scope, builtin_scope: Scope):
        return State(
            None,
            Map({builtin_scope.id: builtin_scope, global_scope.id: global_scope}),
            (global_scope.id, (builtin_scope.id, None)),
            Map(),
            Map(),
            0
        )

    @property
    def current_scope_id(self) -> int:
        return self.scope_stack[0] # type: ignore

    def is_box_in_transaction(self, id: int) -> bool:
        return self.box_in_transaction.get(id, False)

    def infinite_stack(self) -> InfiniteStack:
        """
        Get the scope's stack, but pretend that it's infinitely deep.
        """
        return self.stack # type: ignore

    def push(self, *values: "Value"):
        stack = self.stack
        for value in values:
            stack = (value, stack)
        return self.with_stack(stack)

    def read_box(self, id: int) -> Stack:
        if id not in self.boxes:
            raise RuntimeError(f"Trying to read undefined box with id {id}")
        return self.boxes[id]

    def pop_box(self, id: int) -> Tuple["Value", "State"]:
        v = self.read_box(id)
        if v is None or v[1] is None:
            raise RuntimeError(f"no transaction in process")
        (top, rest) = v
        if rest[1] is None:  # type: ignore
            return top, self.set_box(id, rest)._remove_from_transaction(id)
        else:
            return top, self.set_box(id, rest)

    def commit_box(self, id: int) -> "State":
        v = self.read_box(id)
        if v is None:
            raise RuntimeError(f"no transaction in process")
        (a, rest1) = v
        if rest1 is None:
            raise RuntimeError(f"no transaction in process")
        (_b, rest2) = rest1  # type: ignore
        if rest2 is None:
            return self.set_box(id, (a, None))._remove_from_transaction(id)
        else:
            return self.set_box(id, (a, rest2))

    def set_box(self, id: int, value: Stack) -> "State":
        return self._with_boxes(self.boxes.set(id, value))

    def _put_in_transaction(self, box_id: int) -> "State":
        return self._with_boxes_in_transaction(self.box_in_transaction.set(box_id, True))

    def _remove_from_transaction(self, box_id: int) -> "State":
        if box_id not in self.box_in_transaction:
            return self
        return self._with_boxes_in_transaction(self.box_in_transaction.delete(box_id))

    def with_stack(self, stack: Stack):
        return dataclass_replace(self, stack=stack)

    # def with_scope(self, scope: Scope):
    #     return dataclass_replace(self, scope=scope)

    def _with_boxes(self, boxes: Map):
        return dataclass_replace(self, boxes=boxes)

    def _with_boxes_in_transaction(self, in_transaction: Map):
        return dataclass_replace(self, box_in_transaction=in_transaction)

    def increment_box_id(self):
        return dataclass_replace(self, last_box_id=self.last_box_id + 1)

    def add_box(self, value: "Value") -> Tuple["Box", "State"]:
        state = self.increment_box_id()
        box = Box(state.last_box_id)
        state = state.set_box(state.last_box_id, (value, None))
        return box, state

    def kill_box(self, id: int):
        if id not in self.boxes:
            raise RuntimeError(f"Trying to kill nonexistent box with id {id}")
        return self._with_boxes(self.boxes.delete(id))

    def make_scope(self, parent_id: int, new_id: int) -> "State":
        assert parent_id in self.scopes
        assert new_id not in self.scopes
        new_scope = Scope(parent_id, new_id, Map())
        return dataclass_replace(
            self,
            scopes=self.scopes.set(new_id, new_scope),
            scope_stack=(new_id, self.scope_stack)
        )

    def pop_scope(self) -> "State":
        return dataclass_replace(
            self,
            scope_stack=self.scope_stack[1]
        )

    def get_by_name(self, scope_id: int, name: str) -> "Value":
        if scope_id not in self.scopes:
            raise KeyError(f"No scope #{scope_id} when trying to get {name}, scopestack: {self.scope_stack}")
        return self.scopes[scope_id].get(name, self)

    def look_up_name_in_current_scope(self, name: str) -> "Value":
        return self.get_by_name(self.current_scope_id, name)

    def set_name(self, name: str, value: "Value") -> "State":
        old_scope: Scope = self.scopes[self.current_scope_id]
        new_scope = old_scope.with_member(name, value)
        return dataclass_replace(
            self,
            scopes=self.scopes.set(self.current_scope_id, new_scope)
        )

    def forget_name(self, name: str) -> "State":
        old_scope: Scope = self.scopes[self.current_scope_id]
        new_scope = old_scope.without_member(name)
        return dataclass_replace(
            self,
            scopes=self.scopes.set(self.current_scope_id, new_scope)
        )

    def set_names(self, update: Mapping[str, "Value"]) -> "State":
        old_scope: Scope = self.scopes[self.current_scope_id]
        new_scope = old_scope.with_members(update)
        return dataclass_replace(
            self,
            scopes=self.scopes.set(self.current_scope_id, new_scope)
        )

    def get_scope(self, scope_id: int) -> Optional[Scope]:
        return self.scopes[scope_id]

    def kill_scope(self, scope_id: int) -> "State":
        return dataclass_replace(
            self,
            scopes=self.scopes.delete(scope_id)
        )


@dataclass(frozen=True)
class Put:
    """Put a single value on top of the stack"""
    value: Value
    tag: ClassVar[Literal["put"]] = "put"

    def as_vec(self):
        return Vec((Atom("Put"), self.value))

@dataclass(frozen=True)
class PutCode:
    """Create a closure and put a code value on top of the stack"""
    instructions: Sequence[Instruction]
    source_code: Optional[str] = None
    tag: ClassVar[Literal["put_code"]] = "put_code"

    def as_vec(self):
        rv = (Atom("PutCode"), Vec([i.as_vec() for i in self.instructions]))
        if self.source_code is not None:
            rv += (Str(self.source_code),)
        return Vec(rv)

@dataclass(frozen=True)
class CallByName:
    """Call a function by name"""
    function_name: str
    tag: ClassVar[Literal["call"]] = "call"

    def as_vec(self):
        return Vec((Atom("CallByName"), Str(self.function_name)))

@dataclass(frozen=True)
class CallByValue:
    """Pop a function from the top of the stack and call it"""
    tag: ClassVar[Literal["call_by_value"]] = "call_by_value"

    def as_vec(self):
        return Vec((Atom("CallByValue"),))

@dataclass(frozen=True)
class MakeVec:
    """Collect `size` elements and make a tuple"""
    size: int
    tag: ClassVar[Literal["make_vec"]] = "make_vec"

    def as_vec(self):
        return Vec((Atom("MakeVec"), Int(self.size)))

@dataclass(frozen=True)
class MakeScope:
    """Create a local scope given a parent scope"""
    parent_id: int
    tag: ClassVar[Literal["make_scope"]] = "make_scope"

    def as_vec(self):
        if self.parent_id is None:
            return Vec((Atom("MakeScope"),))
        else:
            return Vec((Atom("MakeScope"), Int(self.parent_id)))

@dataclass(frozen=True)
class PopScope:
    """Discard the topmost scope and return to the parent scope"""
    tag: ClassVar[Literal["pop_scope"]] = "pop_scope"

    def as_vec(self):
        return Vec((Atom("PopScope"),))


# `Instruction` is a single step executed by the interpreter
Instruction = Union[Put, PutCode, CallByName, CallByValue, MakeVec, MakeScope, PopScope]



class CodeFlags(IntFlag):
    """Optimization flags used by `Code`"""
    EMPTY = 0
    PARENT_SCOPE = 1


_atom_cache: Dict[str, Atom] = {}


_bool = bool
class Atom:
    """
    Atom, like :true

    Atoms are cached and compared by identity.
    """
    value: str
    tag: ClassVar[Literal["atom"]] = "atom"

    def __new__(cls, value: str):
        if value in _atom_cache:
            return _atom_cache[value]
        rv = object.__new__(cls)
        rv.__init__(value)
        _atom_cache[value] = rv
        return rv

    def __init__(self, value: str):
        self.value = value

    def __repr__(self):
        return f"Atom({self.value!r})"

    def __eq__(self, other):
        if not isinstance(other, Atom):
            return NotImplemented
        return self.value == other.value

    @staticmethod
    def make(name: str) -> Atom:
        if name not in _atom_cache:
            _atom_cache[name] = Atom(name)
        return _atom_cache[name]

    @staticmethod
    def bool(x: _bool) -> Atom:
        return Atom("true" if x else "false")


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
    """Code value like { :b def :a def b a }"""
    instructions: Sequence[Instruction]
    closure: Optional[int]
    flags: CodeFlags = CodeFlags.EMPTY
    name: str = "λ"
    source_code: Optional[str] = None
    introducer: Optional[weakref.ReferenceType[Callable[[int], Any]]] = None
    finalizer: Optional[weakref.ReferenceType[Callable[[int], Any]]] = None
    tag: ClassVar[Literal["code"]] = "code"

    def introduce(self):
        if self.introducer is not None and self.closure is not None:
            introducer = self.introducer()
            if introducer is not None:
                introducer(self.closure)

    def __del__(self):
        if self.finalizer is not None and self.closure is not None:
            finalizer = self.finalizer()
            if finalizer is not None:
                finalizer(self.closure)

    def with_name(self, name: str) -> Code:
        return dataclass_replace(self, name=name)

@dataclass(frozen=True)
class NativeFunction:
    """A function implemented in Python, like `if` or `+`"""
    fn: Callable[[State], State]
    name: str = "λ"
    tag: ClassVar[Literal["native"]] = "native"

@dataclass(frozen=True)
class Box:
    id: int
    tag: ClassVar[Literal["box"]] = "box"

Value = Union[Atom, Str, Int, Vec, Code, NativeFunction, Box]
