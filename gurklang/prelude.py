import dataclasses
import time
from operator import itemgetter
from typing import Iterable, List

from gurklang.types import *  # type: ignore
from . import stdlib_modules
from .builtin_utils import Module, Fail, make_simple, raw_function
from .vm_utils import stringify_value, render_value_as_source, tuple_equals

module = Module("builtins")

# Shortcuts for brevity
T, V, S = Tuple, Value, Stack


# <`stack` functions>

@module.register_simple()
def dup(stack: T[V, S], scope: Scope, fail: Fail):
    (x, rest) = stack
    return (x, (x, rest)), scope


@module.register_simple()
def drop(stack: T[V, S], scope: Scope, fail: Fail):
    (x, rest) = stack
    return rest, scope


@module.register_simple()
def swap(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (x, (y, rest)) = stack
    return (y, (x, rest)), scope


@module.register_simple()
def tuck(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (x, (y, rest)) = stack
    return (y, (x, (y, rest))), scope


@module.register_simple()
def rot(stack: T[V, T[V, T[V, S]]], scope: Scope, fail: Fail):
    (z, (y, (x, rest))) = stack
    return (x, (z, (y, rest))), scope


@module.register_simple()
def unrot(stack: T[V, T[V, T[V, S]]], scope: Scope, fail: Fail):
    (z, (y, (x, rest))) = stack
    return (y, (x, (z, rest))), scope



@module.register_simple()
def nip(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (y, (x, rest)) = stack
    return (y, rest), scope


@module.register_simple()
def over(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (y, (x, rest)) = stack
    return (x, (y, (x, rest))), scope


@module.register_simple('2dup')
def two_dup(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    y, (x, rest) = stack
    return (y, (x, (y, (x, rest)))), scope


@module.register_simple('2drop')
def two_drop(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (x, rest) = stack
    return rest[1], scope


@module.register_simple('2swap')
def two_swap(stack: T[V, T[V, T[V, T[V, S]]]], scope: Scope, fail: Fail):
    (a, (b, (c, (d, rest)))) = stack
    return (c, (d, (a, (b, rest)))), scope


@module.register_simple('2tuck')
def two_tuck(stack: T[V, T[V, T[V, T[V, S]]]], scope: Scope, fail: Fail):
    (a, (b, (c, (d, rest)))) = stack
    return (c, (d, (a, (b, (c, (d, rest)))))), scope


@module.register_simple('2rot')
def two_rot(stack: T[V, T[V, T[V, T[V, T[V, T[V, S]]]]]], scope: Scope, fail: Fail):
    (a, (b, (c, (d, (e, (f, rest)))))) = stack
    return (c, (d, (e, (f, (a, (b, rest)))))), scope


@module.register_simple('2unrot')
def two_unrot(stack: T[V, T[V, T[V, T[V, T[V, T[V, S]]]]]], scope: Scope, fail: Fail):
    (a, (b, (c, (d, (e, (f, rest)))))) = stack
    return (e, (f, (a, (b, (c, (d, rest)))))), scope


@module.register_simple('2nip')
def two_nip(stack: T[V, T[V, T[V, T[V, S]]]], scope: Scope, fail: Fail):
    (a, (b, (_, (_, rest)))) = stack
    return (a, (b, rest)), scope


@module.register_simple('2over')
def two_over(stack: T[V, T[V, T[V, T[V, S]]]], scope: Scope, fail: Fail):
    (a, (b, (c, (d, rest)))) = stack
    return (c, (d, (a, (b, (c, (d, rest)))))), scope


@module.register_simple()
def concat(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (a, (b, rest)) = stack
    if not a.tag == b.tag == "str":
        fail(f"{render_value_as_source(a)} and {render_value_as_source(b)} must be strings")
    return (Str(b.value + a.value), rest), scope


# </`stack` functions>

@module.register_simple()
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


@module.register_simple("def")
def def_(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    """
    Store a value by a name
    """
    (identifier, (value, rest)) = stack
    if identifier.tag != "atom":
        fail(f"{identifier} is not an atom")
    fn = Code([Put(value)], name=identifier.value, closure=scope, flags=CodeFlags.PARENT_SCOPE)
    return rest, scope.with_member(identifier.value, fn)


@module.register_simple("=")
def equals(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    """Check if two values are equal."""
    (y, (x, rest)) = stack
    if x.tag != y.tag:
        fail(f"cannot compare type {x.tag} with type {y.tag}")
    elif x.tag == "atom":
        fail(f"cannot compare atoms. Use `is` instead")
    elif x.tag in ("str", "int", "code") and x == y:
        return (Atom("true"), rest), scope
    elif x.tag == "vec" and y.tag == "vec":
        return (Atom.bool(tuple_equals(x, y, fail)), rest), scope
    return (Atom("false"), rest), scope


@module.register_simple("not")
def not_(stack: T[V, S], scope: Scope, fail: Fail):
    (head, rest) = stack
    if head is Atom("true"):
        return (Atom("false"), rest), scope
    elif head is Atom("false"):
        return (Atom("true"), rest), scope
    else:
        fail(f"{render_value_as_source(head)} is not a boolean")


@module.register_simple()
def println_string(stack: T[V, S], scope: Scope, fail: Fail):
    (head, rest) = stack
    if head.tag != "str":
        fail(f"{head} is not a string")
    print(head.value)
    return rest, scope


@module.register_simple()
def print_string(stack: T[V, S], scope: Scope, fail: Fail):
    (head, rest) = stack
    if head.tag != "str":
        fail(f"{head} is not a string")
    print(head.value, end="", flush=True)
    return rest, scope


@module.register_simple("input")
def input_(stack: Stack, scope: Scope, fail: Fail):
    return (Str(input()), stack), scope


@module.register_simple()
def prompt(stack: T[V, S], scope: Scope, fail: Fail):
    (head, rest) = stack
    if head.tag != "str":
        fail(f"{head} is not a string")
    text = Str(input(f"{head.value} "))
    return (text, stack), scope


@module.register_simple()
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


@module.register_simple()
def parent_scope(stack: T[V, S], scope: Scope, fail: Fail):
    (code, rest) = stack
    if code.tag != "code":
        fail(f"Expected code value, got: {code}")
    new_code = dataclasses.replace(code, flags=code.flags | CodeFlags.PARENT_SCOPE)
    return (new_code, rest), scope


@module.register_simple("str")
def str_(stack: T[V, S], scope: Scope, fail: Fail):
    (x, rest) = stack
    representation = Str(stringify_value(x))
    return (representation, rest), scope


module.add("!", Code([CallByValue()], closure=None, name="!", flags=CodeFlags.PARENT_SCOPE))


@module.register_simple("if")
def if_(stack: T[V, T[V, T[V, S]]], scope: Scope, fail: Fail):
    (else_, (then, (condition, rest))) = stack
    if condition is Atom("true"):
        return (then, rest), scope
    elif condition is Atom("false"):
        return (else_, rest), scope
    else:
        fail(f"{condition} is not a boolean (:true/:false)")


# <`,` implementation>
@make_simple()
def __spread_vec(stack: T[V, S], scope: Scope, fail: Fail):
    (fn, rest) = stack
    if fn.tag not in ["code", "native"]:
        fail(f"{fn} is not a function")
    sentinel = Atom("{, sentinel}")
    instructions = [Put(sentinel), Put(fn), CallByValue()]
    code = Code(instructions, closure=None, flags=CodeFlags.PARENT_SCOPE, name="--spreader")
    return (code, rest), scope


@make_simple()
def __collect_vec(stack: T[V, S], scope: Scope, fail: Fail):
    head, stack = stack  # type: ignore
    sentinel = Atom("{, sentinel}")
    elements = []
    while head is not sentinel:
        elements.append(head)
        head, stack = stack  # type: ignore
    elements.reverse()
    return (Vec(elements), stack), scope


module.add(
    ",",
    Code(
        [Put(__spread_vec), CallByValue(), CallByValue(), Put(__collect_vec), CallByValue()],
        closure=None,
        flags=CodeFlags.PARENT_SCOPE,
        name=",",
        source_code="{ --spread-vec ! --collect-vec }"
    )
)


# </`,` implementation>


@module.register_simple()
def close(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (function, (value, rest)) = stack

    if function.tag == "code":
        rv = Code([Put(value), *function.instructions], closure=function.closure, name=function.name,
                  flags=function.flags)
    elif function.tag == "native":
        rv = NativeFunction(lambda state: function.fn(State.push(value)), function.name)  # type: ignore
    else:
        fail(f"{function} is not a function")

    return (rv, rest), scope


# <`case` implementation>


Captures = Optional[Tuple[Iterable[Tuple[int, Value]], Dict[str, Value]]]


def _match_with_vec(pattern: Vec, value: Value, fail: Fail) -> Captures:
    if value.tag != "vec":
        return None
    if len(pattern.values) != len(value.values):
        return None
    captures: List[Tuple[int, Value]] = []
    variables: Dict[str, Value] = {}
    for nested_pattern, nested_value in zip(reversed(pattern.values), reversed(value.values)):
        matches = _matches_impl(nested_pattern, nested_value, fail)
        if matches is None:
            return [], {}
        new_captures, new_vars = matches
        if variables.keys() & new_vars.keys():
            fail(f'duplicate variable name in pattern: {variables.keys() & new_vars.keys()!r}')
        captures.extend(new_captures)
        variables.update(new_vars)
    return captures, variables


def _match_with_atom(pattern: Atom, value: Value, fail: Fail) -> Captures:
    label = pattern.value
    if label == '_':
        return [], {}
    elif label.startswith(':'):
        if value == Atom(label[1:]):
            return [], {}
        else:
            return None
    elif frozenset(label) == {'.'}:
        return [(len(label), value)], {}
    elif label[0] == "." and all(map("0123456789".__contains__, label[1:])):
        return [(int(label[1:]), value)], {}
    elif label[0] == ".":
        fail(f"Invalid . pattern: {label}")
    else:
        return [], {label: Code([Put(value)], closure=None)}


def _matches_impl(pattern: Value, value: Value, fail: Fail) -> Captures:
    if isinstance(pattern, Vec):
        return _match_with_vec(pattern, value, fail)
    elif isinstance(pattern, Atom):
        return _match_with_atom(pattern, value, fail)
    elif pattern == value:
        return [], {}
    return None


def _matches(pattern: Vec, stack: Stack, fail: Fail) -> Optional[Tuple[Stack, Dict[str, Value]]]:
    stack_captures: List[Tuple[int, Value]] = []
    variables: Dict[str, Value] = {}
    for inner_pattern in reversed(pattern.values):
        if stack is None:
            return None
        top, stack = stack  # type: ignore
        matches = _matches_impl(inner_pattern, top, fail)
        if matches is None:
            return None
        stack_slots, new_vars = matches
        if new_vars.keys() & variables.keys():
            fail(f'duplicate variable name in pattern: {variables.keys() & new_vars.keys()!r}')
        stack_captures.extend(stack_slots)
        variables.update(new_vars)
    stack_captures.sort(key=itemgetter(0), reverse=True)
    return (
        _stack_extend(stack, (el for _, el in reversed(stack_captures))),
        variables
    )


def _stack_extend(stack: Stack, elems: Iterable[Value]) -> Stack:
    for elem in elems:
        stack = (elem, stack)
    return stack


def _parse_cases(stack: Stack, fail: Fail) -> Tuple[Stack, Sequence[Value], Sequence[Value]]:
    sentinel = Atom('{case sentinel}')
    patterns = []
    actions = []
    is_pattern = False
    while stack[0] is not sentinel: # type: ignore
        next_elem, stack = stack  # type: ignore
        (patterns if is_pattern else actions).append(next_elem)
        is_pattern = not is_pattern
    if len(patterns) != len(actions):
        fail('odd number of forms in case expression, there must be exactly one function per pattern')
    patterns.reverse()
    actions.reverse()
    return stack, patterns, actions


@make_simple()
def __match_case(stack: Stack, scope: Scope, fail: Fail):
    stack, patterns, actions = _parse_cases(stack, fail)
    for pattern, action in zip(patterns, actions):
        if pattern.tag != "vec":
            fail(f'a pattern must be a vector, not {pattern!r}')

        if action.tag != "code":
            fail(f'an action must be code, not {action!r}')

        matched = _matches(pattern, stack[1], fail)
        if matched is None:
            continue

        new_stack, new_variables = matched
        insns = list(action.instructions)
        for k, v in new_variables.items():
            insns[:0] = [Put(v), CallByValue(), Put(Atom(k)), Put(def_), CallByValue()]
        action = Code(instructions=insns, closure=action.closure, flags=action.flags, source_code=action.source_code)
        return (action, new_stack), scope
    return stack, scope


@make_simple()
def __get_case(stack: T[V, S], scope: Scope, fail: Fail):
    sentinel = Atom('{case sentinel}')
    fun, rest = stack
    return (fun, (sentinel, rest)), scope


module.add(
    'case',
    raw_function(
        Put(__get_case), CallByValue(), CallByValue(), Put(__match_case), CallByValue(), CallByValue(),
        name="case"
    )
)


# </`case` implementation>

# <`import` implementation>

def _make_name_getter(lookup: Dict[str, Value], name: str):
    def name_getter(state: State):
        if state.stack is None:
            raise RuntimeError("module getter on an empty stack")
        (name, rest) = state.stack

        if name.tag not in ["atom", "str"]:
            raise RuntimeError(f"member name has to be an atom or a string, got: {name}")

        if name.value not in lookup:
            raise LookupError(f"member {name.value} not found")

        function = lookup[name.value]
        return state.with_stack((function, rest))

    return Code([Put(NativeFunction(name_getter, name)), CallByValue(), CallByValue()], None, CodeFlags.PARENT_SCOPE)


def _import_all(scope: Scope, module: Module):
    return module.members


def _import_qualified(scope: Scope, module: Module, target_name: str):
    return {target_name: _make_name_getter(module.members, target_name)}


def _import_prefixed(scope: Scope, module: Module, prefix: str):
    return {f"{prefix}.{k}": v for k, v in module.members.items()}


def _import_cherrypick(scope: Scope, module: Module, names: Iterable[str]):
    return {name: module.members[name] for name in names}


def _get_imported_members(scope: Scope, module: Module, import_options: Value):
    if import_options is Atom("all"):
        return _import_all(scope, module)

    elif import_options is Atom("qual"):
        return _import_qualified(scope, module, module.name)

    elif import_options is Atom("prefix"):
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


@module.register_simple("import")
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

module.add("print", Code([CallByName("str"), CallByName("print-string")], closure=None, name="print",
                         flags=CodeFlags.PARENT_SCOPE))
module.add("println", Code([CallByName("str"), CallByName("println-string")], closure=None, name="println",
                           flags=CodeFlags.PARENT_SCOPE))
