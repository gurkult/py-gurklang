from immutables import Map
from typing import Any, Callable, Iterator, NoReturn, Optional, TypeVar
from . import vm
from .vm_utils import stringify_value, repr_stack
from . import stdlib_modules
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


def _make_name_getter(lookup: dict[str, Value]):
    def name_getter(stack: Stack, scope: Scope) -> tuple[Stack, Scope]:
        if stack is None:
            raise RuntimeError("module getter on an empty stack")
        (name, rest) = stack

        if name.tag != "atom" and name.tag != "str":
            raise RuntimeError(f"member name has to be an atom or a string, got: {name}")

        if name.value not in lookup:
            raise LookupError(f"member {name.value} not found")

        function = lookup[name.value]
        return vm.call(rest, scope, function)
    return name_getter


@module.register("import")
def import_(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (import_options, (identifier, rest)) = stack

    if identifier.tag != "atom":
        fail(f"module name has to be an atom, got: {identifier}")
    module_name = identifier.value

    try:
        module = next(module for module in stdlib_modules.modules if module.name == module_name)
    except StopIteration:
        module = None

    if module is None:
        fail(f"module {module_name} not found")

    ###

    if import_options == Atom("all"):
        return rest, Scope(scope.parent, scope.id, scope.values.update())

    elif import_options == Atom("qual"):
        name_getter = _make_name_getter(module.members)
        return rest, scope.with_member(module_name, NativeFunction(name_getter))

    elif import_options == Atom("prefix"):
        imports = {f"{module_name}.{k}": v for k, v in module.members.items()}
        return rest, Scope(scope.parent, scope.id, scope.values.update(imports))

    elif import_options.tag == "atom" and import_options.value.startswith("as:"):
        new_name = import_options.value[len("as:"):]
        name_getter = _make_name_getter(module.members)
        return rest, scope.with_member(new_name, NativeFunction(name_getter))

    elif import_options.tag == "atom" and import_options.value.startswith("prefix:"):
        prefix = import_options.value[len("prefix:"):]
        imports = {f"{prefix}.{k}": v for k, v in module.members.items()}
        return rest, Scope(scope.parent, scope.id, scope.values.update(imports))

    elif import_options.tag == "vec" and all(x.tag == "atom" for x in import_options.values):
        names: list[str] = [x.value for x in import_options.values]
        imports = {name: module.members[name] for name in names}
        return rest, Scope(scope.parent, scope.id, scope.values.update(imports))

    else:
        fail(f"Invalid import options: {import_options}")





module.add("print", Code([Call("str"), Call("print_string")], closure=None))
