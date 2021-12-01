from functools import reduce
from typing import TypeVar, Tuple

from ..builtin_utils import BuiltinModule, Fail, make_function, raw_function, make_simple
from ..types import CallByValue, Put, State, Str, Value, Stack, Int, Atom, Vec
from ..vm_utils import render_value_as_source

module = BuiltinModule("strings")
T, V, S = Tuple, Value, Stack
Z = TypeVar("Z", bound=Stack)

_UNARY_STRING_TO_STRING = [
    ('casefold', 'fold-case'),
    ('lower', '->lower'),
    ('upper', '->upper'),
    ('swapcase', 'swap-case'),
    ('title', '->title'),
]
_UNARY_STRING_TO_BOOL = [
    ('is' + w, w + '?')
    for w in 'alnum alpha ascii decimal digit identifier lower numeric printable space title upper'.split()
]


def _register_delegated_methods():
    for function, name in _UNARY_STRING_TO_STRING:
        method = getattr(str, function)

        #  closures capture by name, so not passing method as a default argument would only use the last method
        @module.register_simple(name)
        def fun(stack: T[V, S], fail: Fail, method=method):
            arg, rest = stack
            if arg.tag != 'str':
                fail('argument is not a string')
            return Str(method(arg.value)), rest

    for function, name in _UNARY_STRING_TO_BOOL:
        method = getattr(str, function)

        #  closures capture by name, so not passing method as a default argument would only use the last method
        @module.register_simple(name)
        def fun(stack: T[V, S], fail: Fail, method=method):
            arg, rest = stack
            if arg.tag != 'str':
                fail('argument is not a string')
            return Atom.bool(method(arg.value)), rest


_register_delegated_methods()


@module.register_simple()
def join_list(stack: T[V, T[V, S]], fail: Fail):
    sep, (strs, rest) = stack
    if sep.tag != 'str':
        fail('join requires a string as a separator')
    if strs.tag != 'vec':
        fail('join requires a list of strings as its argument')
    el = strs.values
    strings = []
    while len(el) != 0:
        if len(el) != 2:
            fail('a list must be composed of 2 long tuples')
        car, cdr = el
        if cdr.tag != 'vec':
            fail('a list must only contain tuples as the second element')
        if car.tag != 'str':
            fail('all elements of the list passed to join must be strings')
        strings.append(car.value)
        el = cdr.values
    return Str(sep.value.join(strings)), rest


@module.register_simple()
def split(stack: T[V, T[V, S]], fail: Fail):
    sep, (string, rest) = stack
    if sep.tag != 'str':
        fail('join requires a string as a separator')
    if string.tag != 'str':
        fail('join requires a string to split')
    flat = [Str(s) for s in string.value.split(sep.value)]
    nested = reduce(lambda a, b: Vec([b, a]), reversed(flat), Vec([]))
    return nested, rest


@module.register_simple()
def replace(stack: T[V, T[V, T[V, S]]], fail: Fail):
    new, (old, (s, rest)) = stack
    if s.tag != "str" or old.tag != "str" or new.tag != "str":
        fail(f"{render_value_as_source(s)}, {render_value_as_source(old)} and {render_value_as_source(new)} must be strings")
    return Str(s.value.replace(old.value, new.value)), rest


@make_simple()
def __foreach_str_init(stack: T[V, T[V, S]], fail: Fail):
    (fn, (s, rest)) = stack
    if s.tag != "str":
        fail(f"{render_value_as_source(s)} is not a string")

    if fn.tag != "code" and fn.tag != "native":
        fail(f"{render_value_as_source(fn)} is not a function")

    return (__foreach_str_step, (Int(0), (fn, (s, rest))))


@make_function()
def __foreach_str_step(state: State, fail: Fail) -> State:
    (index, (fn, (s, rest))) = state.infinite_stack()
    assert index.tag == "int"
    assert fn.tag == "code" or fn.tag == "native"
    assert s.tag == "str"

    if index.value >= len(s.value):
        identity = raw_function(source_code="{}")
        return (state
                .with_stack(rest)
                .push(identity)
                .push(identity))

    return (state
            .with_stack(rest)
            .push(s)
            .push(fn)
            .push(Int(index.value + 1))
            .push(__bootstrap_foreach_step)
            .push(Str(s.value[index.value]))
            .push(fn))


__bootstrap_foreach_step = raw_function(
    Put(__foreach_str_step),
    CallByValue(),
    CallByValue(),
    CallByValue(),
    name="--bootstrap-foreach-step"
)
foreach_str = raw_function(
    Put(__foreach_str_init),
    CallByValue(),
    CallByValue(),
    CallByValue(),
    CallByValue(),
    name="foreach-str"
)
module.add("foreach-str", foreach_str)
module.add("∀s", foreach_str)


@module.register_simple('str->int')
def parse_int(stack: T[V, S], fail:Fail):
    v, rest = stack
    if v.tag != 'str':
        fail("str->int requires a string")
    return Int(int(v.value)), rest