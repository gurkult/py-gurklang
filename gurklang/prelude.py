from operator import itemgetter

from . import vm
import time
import dataclasses
from typing import Iterable, Dict, List, Tuple
from . import stdlib_modules
from gurklang.types import CallByValue, CodeFlags, Scope, Stack, Put, CallByName, Value, Atom, Str, Code, \
    NativeFunction, Vec
from .builtin_utils import Module, Fail
from .vm_utils import stringify_value

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


module.add("!", Code([CallByValue()], closure=None, flags=CodeFlags.PARENT_SCOPE))


@module.register("if")
def if_(stack: T[V, T[V, T[V, S]]], scope: Scope, fail: Fail):
    (else_, (then, (condition, rest))) = stack
    if condition == Atom.make("true"):
        return (then, rest), scope
    elif condition == Atom.make("false"):
        return (else_, rest), scope
    else:
        fail(f"{condition} is not a boolean (:true/:false)")


@module.register()
def close(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (function, (value, rest)) = stack

    if function.tag == "code":
        rv = Code([Put(value), *function.instructions], closure=function.closure, flags=function.flags)
    elif function.tag == "native":
        rv = NativeFunction(lambda st, sc: function.fn((value, st), sc))  # type: ignore
    else:
        fail(f"{function} is not a function")

    return (rv, rest), scope


# <`case` implementation>

def _matches_impl(
        pattern: Value,
        value: Value,
        fail: Fail
) -> Tuple[bool, Iterable[Tuple[int, Value]], Dict[str, Value]]:
    if isinstance(pattern, Vec) and isinstance(value, Vec):
        captures: List[tuple[int, Value]] = []
        variables: Dict[str, Value] = {}
        for nested_pattern, nested_value in zip(pattern.values, value.values):
            matches, new_captures, new_variables = _matches_impl(nested_pattern, nested_value, fail)
            if not matches:
                return False, [], {}
            if variables.keys() & new_variables.keys():
                fail(f'duplicate variable name in pattern: {variables.keys() & new_variables.keys()!r}')
            captures.extend(new_captures)
            variables.update(new_variables)
        return True, captures, variables
    elif isinstance(pattern, Atom):
        label = pattern.value
        if label.startswith(':') and isinstance(value, Atom) and value.value == label[1:]:
            return True, [], {}
        elif frozenset(label) == {'.'}:
            return True, [(len(label), value)], {}
        else:
            return True, [], {label: Code([Put(value)], closure=None)}
    elif pattern == value:
        return True, [], {}
    return False, [], {}


def _matches(pattern: Vec, stack: Stack, fail: Fail) -> Tuple[bool, Stack, Dict[str, Value]]:
    captures: List[Tuple[int, Value]] = []
    variables: Dict[str, Value] = {}
    original_stack = stack
    for inner_pattern in reversed(pattern.values):
        top, stack = stack
        matches, stack_slots, new_vars = _matches_impl(inner_pattern, top, fail)
        if not matches:
            return False, original_stack, {}
        if new_vars.keys() & variables.keys():
            fail(f'duplicate variable name in pattern: {variables.keys() & new_vars.keys()!r}')
        captures.extend(stack_slots)
        variables.update(new_vars)
    print(captures)
    captures.sort(key=itemgetter(0), reverse=True)
    print(captures)
    return (
        True,
        _stack_extend(stack, (el for _, el in reversed(captures))),
        variables
    )


def _stack_extend(stack: Stack, elems: Iterable[Value]) -> Stack:
    for elem in elems:
        stack = (elem, stack)
    return stack


@module.register()
def case(stack: T[V, S], scope: Scope, fail: Fail):
    sentinel = Atom(object())  # type: ignore
    fun, rest = stack
    new_stack, _ = vm.call((sentinel, rest), scope, fun)
    cases = []
    while not (isinstance(new_stack[0], Atom) and new_stack[0].value is sentinel.value):
        next_elem, new_stack = new_stack
        cases.append(next_elem)
    if len(cases) % 2 == 1:
        fail('odd number of forms in case expression, there must be exactly one function per pattern')
    for action, pattern in zip(cases[::2], cases[1::2]):
        if not isinstance(pattern, Vec):
            fail(f'a pattern must be a vector, not {pattern!r}')
        matched, new_stack, new_variables = _matches(pattern, rest, fail)
        if matched:
            return vm.call(new_stack, scope.with_members(new_variables), action)
    return stack, scope


# </`case` implementation>

# <`import` implementation>

def _make_name_getter(lookup: Dict[str, Value]):
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
    return Code([Put(NativeFunction(name_getter)),  CallByValue()], None, CodeFlags.PARENT_SCOPE)


def _import_all(scope: Scope, module: Module):
    return module.members


def _import_qualified(scope: Scope, module: Module, target_name: str):
    return {target_name: _make_name_getter(module.members)}


def _import_prefixed(scope: Scope, module: Module, prefix: str):
    return {f"{prefix}.{k}": v for k, v in module.members.items()}


def _import_cherrypick(scope: Scope, module: Module, names: Iterable[str]):
    return {name: module.members[name] for name in names}


def _get_imported_members(scope: Scope, module: Module, import_options: Value):
    if import_options == Atom.make("all"):
        return _import_all(scope, module)

    elif import_options == Atom.make("qual"):
        return _import_qualified(scope, module, module.name)

    elif import_options == Atom.make("prefix"):
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

module.add("print", Code([CallByName("str"), CallByName("print-string")], closure=None, flags=CodeFlags.PARENT_SCOPE))
module.add("println", Code([CallByName("str"), CallByName("println-string")], closure=None, flags=CodeFlags.PARENT_SCOPE))
