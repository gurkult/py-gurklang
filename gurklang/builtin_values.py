from immutables import Map
from typing import Any, Callable, Iterator, NoReturn, Optional, TypeVar
from . import vm
from .vm_utils import stringify_value, repr_stack
from gurklang.types import (
    Scope, Stack,

    Put, Call,

    Value,
    Atom, Int, Str, Code, NativeFunction,
)
from .builtin_utils import Module, Fail


module = Module("builtins")


# Shortcuts for brevity
T, V, S = tuple, Value, Stack


@module.register()
def dup(stack: T[V, S], scope: Scope, fail: Fail):
    (x, rest) = stack
    return (x, (x, rest)), scope


@module.register()
def swap(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (x, (y, rest)) = stack
    return (y, (x, rest)), scope


@module.register()
def rot3(stack: T[V, T[V, T[V, S]]], scope: Scope, fail: Fail):
    (z, (y, (x, rest))) = stack
    return (x, (y, (z, rest))), scope


@module.register()
def jar(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    """
    Store a function by a name
    """
    (identifier, (code, rest)) = stack
    if identifier.tag != "atom":
        fail(f"{identifier} is not an atom")
    if code.tag != "code" and code.tag != "native":
        fail(f"{code} is not code")
    return rest, scope.with_member(identifier.value, code)


@module.register()
def var(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    """
    Store a value by a name
    """
    (identifier, (value, rest)) = stack
    if identifier.tag != "atom":
        fail(f"{identifier} is not an atom")
    fn = Code([Put(value)], closure=scope)
    return rest, scope.with_member(identifier.value, fn)


@module.register()
def print_string(stack: T[V, S], scope: Scope, fail: Fail):
    (head, rest) = stack
    if head.tag != "str":
        fail(f"{head} is not a string")
    print(head.value)
    return rest, scope


@module.register("str")
def str_(stack: T[V, S], scope: Scope, fail: Fail):
    (x, rest) = stack
    representation = Str(stringify_value(x))
    return (representation, rest), scope


@module.register("+")
def add(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (x, (y, rest)) = stack
    if x.tag != "int" or y.tag != "int":
        fail(f"{x} cannot be added with {y}")
    return (Int(x.value + y.value), rest), scope


@module.register("!")
def exclamation_mark(stack: T[V, S], scope: Scope, fail: Fail):
    (function, rest) = stack
    return vm.call(rest, scope, function)


@module.register("if")
def if_(stack: T[V, T[V, T[V, S]]], scope: Scope, fail: Fail):
    (condition, (else_, (then, rest))) = stack
    if condition == Atom("true"):
        return vm.call(rest, scope, then)
    elif condition == Atom("false"):
        return vm.call(rest, scope, else_)
    else:
        fail(f"{condition} is not a boolean (:true/:false)")


module.add("print", Code([Call("str"), Call("print_string")], closure=None))
