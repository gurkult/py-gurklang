from .types import Scope, Stack, Value, Vec
from typing import Any, Iterator, List, Dict


def stringify_value(v: Value, depth: int = 0):
    if depth >= 42:
        return "∞"

    if v.tag == "str":
        return v.value
    elif v.tag == "int":
        return str(v.value)
    elif v.tag == "atom":
        return ":" + v.value
    elif v.tag == "code":
        if v.name == "λ" and v.source_code is not None:
            return v.source_code
        elif v.name == "λ":
            return "{...}"
        else:
            return v.name
    elif v.tag == "vec":
        return "(" + " ".join(
            x.value if x.tag == "atom" else render_value_as_source(x, depth + 1)
            for x in v.values
        ) + ")"
    elif v.tag == "native":
        return f"`{v.name}`"
    elif v.tag == "box":
        return f"`box({v.id})`"
    else:
        raise RuntimeError(v)


def render_value_as_source(v: Value, depth: int = 0):
    if depth >= 42:
        return "∞"

    if v.tag == "str":
        return repr(v.value)
    else:
        return stringify_value(v, depth + 1)


def unwrap_stack(stack: Stack) -> Iterator[Value]:
    while stack is not None:
        x, stack = stack  # type: ignore
        yield x


def repr_stack(stack) -> List[Value]:
    return [*unwrap_stack(stack)][::-1]


def stringify_stack(stack: Stack, max_depth: int = 0):
    if stack is None:
        return "()"
    elif max_depth <= 0:
        return "∞"
    else:
        head, rest = stack
        return f"({render_value_as_source(head)} {stringify_stack(rest, max_depth - 1)})"


def tuple_equals(x: Vec, y: Vec, fail) -> bool:
    if len(x.values) != len(y.values):
        fail(f"Tuples {render_value_as_source(x)} and {render_value_as_source(y)} are of different lengths")
    for x_val, y_val in zip(x.values, y.values):
        if x_val.tag != y_val.tag:
            fail(f"{render_value_as_source(x_val)} and {render_value_as_source(y_val)} are of different types")
        elif x_val.tag == "vec" and y_val.tag == "vec": # TODO @decorator-factory: pyright bug updates?
            if not tuple_equals(x_val, y_val, fail):
                return False
        elif x_val != y_val:
            return False
    return True
