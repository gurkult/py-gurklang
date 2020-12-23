import time
import dataclasses
from typing import Iterable, Dict, List, Tuple
from .vm_utils import stringify_value
from . import stdlib_modules
from gurklang.types import CallByValue, CodeFlags, Scope, Stack, Put, CallByName, Value, Atom, Str, Code, NativeFunction, Vec
from .builtin_utils import Module, Fail, make_function


module = Module("builtins")


# Shortcuts for brevity
T, V, S = Tuple, Value, Stack


@module.register()
def dup(stack: T[V, S], scope: Scope, fail: Fail):
    (x, rest) = stack
    return (x, (x, rest)), scope


@module.register()
def drop(stack: T[V, S], scope: Scope, fail: Fail):
    (x, rest) = stack
    return rest, scope


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

    if code.tag not in ["code", "native"]:
        fail(f"{code} is not code")

    if code.tag == "code":
        code = code.with_name(identifier.value)

    return rest, scope.with_member(identifier.value, code)


@module.register()
def var(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    """
    Store a value by a name
    """
    (identifier, (value, rest)) = stack
    if identifier.tag != "atom":
        fail(f"{identifier} is not an atom")
    fn = Code([Put(value)], name=identifier.value, closure=scope)
    return rest, scope.with_member(identifier.value, fn)


@module.register()
def println_string(stack: T[V, S], scope: Scope, fail: Fail):
    (head, rest) = stack
    if head.tag != "str":
        fail(f"{head} is not a string")
    print(head.value)
    return rest, scope


@module.register()
def print_string(stack: T[V, S], scope: Scope, fail: Fail):
    (head, rest) = stack
    if head.tag != "str":
        fail(f"{head} is not a string")
    print(head.value, end="", flush=True)
    return rest, scope


@module.register("input")
def input_(stack: Stack, scope: Scope, fail: Fail):
    return (Str(input()), stack), scope


@module.register()
def prompt(stack: T[V, S], scope: Scope, fail: Fail):
    (head, rest) = stack
    if head.tag != "str":
        fail(f"{head} is not a string")
    text = Str(input(f"{head.value} "))
    return (text, stack), scope


@module.register()
def sleep(stack: T[V, S], scope: Scope, fail: Fail):
    (head, rest) = stack
    if head.tag == "int":
        sleep_time = head.value
    elif head.tag == "vec" and len(head.values) == 2 and head.values[0].tag == "int" and head.values[1].tag == "int":
        sleep_time: float = head.values[0].value / head.values[1].value
    else:
        fail(f"Invalid duration: {head}")
    time.sleep(sleep_time)
    return rest, scope


@module.register()
def parent_scope(stack: T[V, S], scope: Scope, fail: Fail):
    (code, rest) = stack
    if code.tag != "code":
        fail(f"Expected code value, got: {code}")
    new_code = dataclasses.replace(code, flags=code.flags | CodeFlags.PARENT_SCOPE)
    return (new_code, rest), scope


@module.register("str")
def str_(stack: T[V, S], scope: Scope, fail: Fail):
    (x, rest) = stack
    representation = Str(stringify_value(x))
    return (representation, rest), scope


module.add("!", Code([CallByValue()], closure=None, name="!", flags=CodeFlags.PARENT_SCOPE))


@module.register("if")
def if_(stack: T[V, T[V, T[V, S]]], scope: Scope, fail: Fail):
    (else_, (then, (condition, rest))) = stack
    if condition is Atom.make("true"):
        return (then, rest), scope
    elif condition is Atom.make("false"):
        return (else_, rest), scope
    else:
        fail(f"{condition} is not a boolean (:true/:false)")


# <`,` implementation>
@make_function()
def __spread_vec(stack: T[V, S], scope: Scope, fail: Fail):
    (fn, rest) = stack
    if fn.tag not in ["code", "native"]:
        fail(f"{fn} is not a function")
    sentinel = Atom.make("{, sentinel}")
    instructions = [Put(sentinel), Put(fn), CallByValue()]
    code = Code(instructions, closure=None, flags=CodeFlags.PARENT_SCOPE, name="--spreader")
    return (code, rest), scope

@make_function()
def __collect_vec(stack: T[V, S], scope: Scope, fail: Fail):
    head, stack = stack  # type: ignore
    sentinel = Atom.make("{, sentinel}")
    elements = []
    while head is not sentinel:
        elements.append(head)
        head, stack = stack  # type: ignore
    elements.reverse()
    return (Vec(elements), stack), scope

module.add(
    ",",
    Code(
        [Put(__spread_vec), CallByValue(), CallByValue(), Put(__collect_vec),CallByValue()],
        closure=None,
        flags=CodeFlags.PARENT_SCOPE,
        name=",",
        source_code="{ --spread-vec ! --collect-vec }"
    )
)
# </`,` implementation>


@module.register()
def close(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (function, (value, rest)) = stack

    if function.tag == "code":
        rv = Code([Put(value), *function.instructions], closure=function.closure, name=function.name, flags=function.flags)
    elif function.tag == "native":
        rv = NativeFunction(lambda st, sc: function.fn((value, st), sc), function.name)  # type: ignore
    else:
        fail(f"{function} is not a function")

    return (rv, rest), scope


# <`import` implementation>

def _make_name_getter(lookup: Dict[str, Value], name: str):
    def name_getter(stack: Stack, scope: Scope):
        if stack is None:
            raise RuntimeError("module getter on an empty stack")
        (name, rest) = stack

        if name.tag not in ["atom", "str"]:
            raise RuntimeError(f"member name has to be an atom or a string, got: {name}")

        if name.value not in lookup:
            raise LookupError(f"member {name.value} not found")

        function = lookup[name.value]
        return (function, rest), scope
    return Code([Put(NativeFunction(name_getter, name)),  CallByValue()], None, CodeFlags.PARENT_SCOPE)


def _import_all(scope: Scope, module: Module):
    return module.members


def _import_qualified(scope: Scope, module: Module, target_name: str):
    return {target_name: _make_name_getter(module.members, target_name)}


def _import_prefixed(scope: Scope, module: Module, prefix: str):
    return {f"{prefix}.{k}": v for k, v in module.members.items()}


def _import_cherrypick(scope: Scope, module: Module, names: Iterable[str]):
    return {name: module.members[name] for name in names}


def _get_imported_members(scope: Scope, module: Module, import_options: Value):
    if import_options is Atom.make("all"):
        return _import_all(scope, module)

    elif import_options is Atom.make("qual"):
        return _import_qualified(scope, module, module.name)

    elif import_options is Atom.make("prefix"):
        return _import_prefixed(scope, module, module.name)

    elif import_options.tag == "atom" and import_options.value.startswith("as:"):
        new_name = import_options.value[len("as:"):]
        return _import_qualified(scope, module, new_name)

    elif import_options.tag == "atom" and import_options.value.startswith("prefix:"):
        prefix = import_options.value[len("prefix:"):]
        return _import_prefixed(scope, module, prefix)

    elif import_options.tag == "vec" and all(x.tag == "atom" for x in import_options.values):
        names: List[str] = [x.value for x in import_options.values]
        return _import_cherrypick(scope, module, names)

    else:
        return None


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

    new_members = _get_imported_members(scope, module, import_options)

    if new_members is None:
        fail(f"invalid import options: {import_options}")

    return rest, scope.with_members(new_members)






# </`import` implementation>

module.add("print", Code([CallByName("str"), CallByName("print-string")], closure=None, name="print", flags=CodeFlags.PARENT_SCOPE))
module.add("println", Code([CallByName("str"), CallByName("println-string")], closure=None, name="println", flags=CodeFlags.PARENT_SCOPE))
