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
def dup(stack: T[V, S], fail: Fail):
    (x, rest) = stack
    return (x, (x, rest))


@module.register_simple()
def drop(stack: T[V, S], fail: Fail):
    (x, rest) = stack
    return rest


@module.register_simple()
def swap(stack: T[V, T[V, S]], fail: Fail):
    (x, (y, rest)) = stack
    return (y, (x, rest))


@module.register_simple()
def tuck(stack: T[V, T[V, S]], fail: Fail):
    (x, (y, rest)) = stack
    return (y, (x, (y, rest)))


@module.register_simple()
def rot(stack: T[V, T[V, T[V, S]]], fail: Fail):
    (z, (y, (x, rest))) = stack
    return (x, (z, (y, rest)))


@module.register_simple()
def unrot(stack: T[V, T[V, T[V, S]]], fail: Fail):
    (z, (y, (x, rest))) = stack
    return (y, (x, (z, rest)))



@module.register_simple()
def nip(stack: T[V, T[V, S]], fail: Fail):
    (y, (x, rest)) = stack
    return (y, rest)


@module.register_simple()
def over(stack: T[V, T[V, S]], fail: Fail):
    (y, (x, rest)) = stack
    return (x, (y, (x, rest)))


@module.register_simple('2dup')
def two_dup(stack: T[V, T[V, S]], fail: Fail):
    y, (x, rest) = stack
    return (y, (x, (y, (x, rest))))


@module.register_simple('2drop')
def two_drop(stack: T[V, T[V, S]], fail: Fail):
    (x, rest) = stack
    return rest[1]


@module.register_simple('2swap')
def two_swap(stack: T[V, T[V, T[V, T[V, S]]]], fail: Fail):
    (a, (b, (c, (d, rest)))) = stack
    return (c, (d, (a, (b, rest))))


@module.register_simple('2tuck')
def two_tuck(stack: T[V, T[V, T[V, T[V, S]]]], fail: Fail):
    (a, (b, (c, (d, rest)))) = stack
    return (c, (d, (a, (b, (c, (d, rest))))))


@module.register_simple('2rot')
def two_rot(stack: T[V, T[V, T[V, T[V, T[V, T[V, S]]]]]], fail: Fail):
    (a, (b, (c, (d, (e, (f, rest)))))) = stack
    return (c, (d, (e, (f, (a, (b, rest))))))


@module.register_simple('2unrot')
def two_unrot(stack: T[V, T[V, T[V, T[V, T[V, T[V, S]]]]]], fail: Fail):
    (a, (b, (c, (d, (e, (f, rest)))))) = stack
    return (e, (f, (a, (b, (c, (d, rest))))))


@module.register_simple('2nip')
def two_nip(stack: T[V, T[V, T[V, T[V, S]]]], fail: Fail):
    (a, (b, (_, (_, rest)))) = stack
    return (a, (b, rest))


@module.register_simple('2over')
def two_over(stack: T[V, T[V, T[V, T[V, S]]]], fail: Fail):
    (a, (b, (c, (d, rest)))) = stack
    return (c, (d, (a, (b, (c, (d, rest))))))


@module.register_simple()
def concat(stack: T[V, T[V, S]], fail: Fail):
    (a, (b, rest)) = stack
    if a.tag != "str" or b.tag != "str":
        fail(f"{render_value_as_source(a)} and {render_value_as_source(b)} must be strings")
    return (Str(b.value + a.value), rest)


# </`stack` functions>

@module.register()
def jar(state: State, fail: Fail):
    """
    Store a function by a name
    """
    (identifier, (code, rest)) = state.infinite_stack()
    if identifier.tag != "atom":
        fail(f"{identifier} is not an atom")

    if code.tag not in ["code", "native"]:
        fail(f"{code} is not code")

    if code.tag == "code":
        code = code.with_name(identifier.value)

    return state.with_stack(rest).set_name(identifier.value, code)


@module.register("def")
def def_(state: State, fail: Fail):
    """
    Store a value by a name
    """
    (identifier, (value, rest)) = state.infinite_stack()
    if identifier.tag != "atom":
        fail(f"{identifier} is not an atom")
    fn = Code([Put(value)], closure=None, flags=CodeFlags.PARENT_SCOPE)
    return state.with_stack(rest).set_name(identifier.value, fn)


@module.register_simple("=")
def equals(stack: T[V, T[V, S]], fail: Fail):
    """Check if two values are equal."""
    (y, (x, rest)) = stack
    if x.tag != y.tag:
        fail(f"cannot compare type {x.tag} with type {y.tag}")
    elif x.tag == "atom":
        fail(f"cannot compare atoms. Use `is` instead")
    elif x.tag in ("str", "int", "code") and x == y:
        return (Atom("true"), rest)
    elif x.tag == "vec" and y.tag == "vec":
        return (Atom.bool(tuple_equals(x, y, fail)), rest)
    return (Atom("false"), rest)


@module.register_simple("not")
def not_(stack: T[V, S], fail: Fail):
    (head, rest) = stack
    if head is Atom("true"):
        return (Atom("false"), rest)
    elif head is Atom("false"):
        return (Atom("true"), rest)
    else:
        fail(f"{render_value_as_source(head)} is not a boolean")


@module.register_simple()
def println_string(stack: T[V, S], fail: Fail):
    (head, rest) = stack
    if head.tag != "str":
        fail(f"{head} is not a string")
    print(head.value)
    return rest


@module.register_simple()
def print_string(stack: T[V, S], fail: Fail):
    (head, rest) = stack
    if head.tag != "str":
        fail(f"{head} is not a string")
    print(head.value, end="", flush=True)
    return rest


@module.register_simple("input")
def input_(stack: Stack, fail: Fail):
    return (Str(input()), stack)


@module.register_simple()
def prompt(stack: T[V, S], fail: Fail):
    (head, rest) = stack
    if head.tag != "str":
        fail(f"{head} is not a string")
    text = Str(input(f"{head.value} "))
    return (text, rest)


@module.register_simple()
def sleep(stack: T[V, S], fail: Fail):
    (head, rest) = stack
    if head.tag == "int":
        sleep_time = head.value
    elif head.tag == "vec" and len(head.values) == 2 and head.values[0].tag == "int" and head.values[1].tag == "int":
        sleep_time: float = head.values[0].value / head.values[1].value
    else:
        fail(f"Invalid duration: {head}")
    time.sleep(sleep_time)
    return rest


@module.register_simple()
def parent_scope(stack: T[V, S], fail: Fail):
    (code, rest) = stack
    if code.tag != "code":
        fail(f"Expected code value, got: {code}")
    new_code = dataclasses.replace(code, flags=code.flags | CodeFlags.PARENT_SCOPE)
    return (new_code, rest)


@module.register_simple("str")
def str_(stack: T[V, S], fail: Fail):
    (x, rest) = stack
    representation = Str(stringify_value(x))
    return (representation, rest)


module.add("!", Code([CallByValue()], closure=None, name="!", flags=CodeFlags.PARENT_SCOPE))


@module.register_simple("if")
def if_(stack: T[V, T[V, T[V, S]]], fail: Fail):
    (else_, (then, (condition, rest))) = stack
    if condition is Atom("true"):
        return (then, rest)
    elif condition is Atom("false"):
        return (else_, rest)
    else:
        fail(f"{condition} is not a boolean (:true/:false)")


# <`,` implementation>
@make_simple()
def __spread_vec(stack: T[V, S], fail: Fail):
    (fn, rest) = stack
    if fn.tag not in ["code", "native"]:
        fail(f"{fn} is not a function")
    sentinel = Atom("{, sentinel}")
    instructions = [Put(sentinel), Put(fn), CallByValue()]
    code = Code(instructions, closure=None, flags=CodeFlags.PARENT_SCOPE, name="--spreader")
    return (code, rest)


@make_simple()
def __collect_vec(stack: T[V, S], fail: Fail):
    head, stack = stack  # type: ignore
    sentinel = Atom("{, sentinel}")
    elements = []
    while head is not sentinel:
        elements.append(head)
        head, stack = stack  # type: ignore
    elements.reverse()
    return (Vec(elements), stack)


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
def close(stack: T[V, T[V, S]], fail: Fail):
    (function, (value, rest)) = stack

    if function.tag == "code":
        function.introduce()
        rv = Code([Put(value), *function.instructions], closure=function.closure, name=function.name,
                  flags=function.flags, finalizer=function.finalizer, introducer=function.introducer)
    elif function.tag == "native":
        rv = NativeFunction(lambda state: function.fn(state.push(value)), function.name)  # type: ignore
    else:
        fail(f"{function} is not a function")

    return (rv, rest)


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
def __match_case(stack: Stack, fail: Fail):
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
        action.introduce()
        action = Code(
            instructions=insns,
            closure=action.closure,
            flags=action.flags,
            source_code=action.source_code,
            finalizer=action.finalizer,
            introducer=action.introducer
        )
        return (action, new_stack)
    return stack


@make_simple()
def __get_case(stack: T[V, S], fail: Fail):
    sentinel = Atom('{case sentinel}')
    fun, rest = stack
    return (fun, (sentinel, rest))


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

        if name.tag != "atom" and name.tag != "str":
            raise RuntimeError(f"member name has to be an atom or a string, got: {name}")

        if name.value not in lookup:
            raise LookupError(f"member {name.value} not found")

        function = lookup[name.value]
        return state.with_stack((function, rest))

    return Code([Put(NativeFunction(name_getter, name)), CallByValue(), CallByValue()], None, CodeFlags.PARENT_SCOPE)


def _import_all(module: Module):
    return module.members


def _import_qualified(module: Module, target_name: str):
    return {target_name: _make_name_getter(module.members, target_name)}


def _import_prefixed(module: Module, prefix: str):
    return {f"{prefix}.{k}": v for k, v in module.members.items()}


def _import_cherrypick(module: Module, names: Iterable[str]):
    return {name: module.members[name] for name in names}


def _get_imported_members(module: Module, import_options: Value):
    if import_options is Atom("all"):
        return _import_all(module)

    elif import_options is Atom("qual"):
        return _import_qualified(module, module.name)

    elif import_options is Atom("prefix"):
        return _import_prefixed(module, module.name)

    elif import_options.tag == "atom" and import_options.value.startswith("as:"):
        new_name = import_options.value[len("as:"):]
        return _import_qualified(module, new_name)

    elif import_options.tag == "atom" and import_options.value.startswith("prefix:"):
        prefix = import_options.value[len("prefix:"):]
        return _import_prefixed(module, prefix)

    elif import_options.tag == "vec" and all(x.tag == "atom" for x in import_options.values):
        names: List[str] = [x.value for x in import_options.values]
        return _import_cherrypick(module, names)

    else:
        return None


@module.register("import")
def import_(state: State, fail: Fail):
    (import_options, (identifier, rest)) = state.infinite_stack()

    if identifier.tag != "atom":
        fail(f"module name has to be an atom, got: {identifier}")
    module_name = identifier.value

    try:
        module = next(module for module in stdlib_modules.modules if module.name == module_name)
    except StopIteration:
        module = None

    if module is None:
        fail(f"module {module_name} not found")

    new_members = _get_imported_members(module, import_options)

    if new_members is None:
        fail(f"invalid import options: {import_options}")

    return state.with_stack(rest).set_names(new_members)


# </`import` implementation>

module.add("print", Code([CallByName("str"), CallByName("print-string")], closure=None, name="print",
                         flags=CodeFlags.PARENT_SCOPE))
module.add("println", Code([CallByName("str"), CallByName("println-string")], closure=None, name="println",
                           flags=CodeFlags.PARENT_SCOPE))
