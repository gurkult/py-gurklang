from typing import Union
from .types import Atom, Scope, Stack, Value, Vec
from typing import Any, Iterator, List, Dict, Literal


def stringify_value(v: Value):
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
        return "(" + " ".join(map(stringify_value, v.values)) + ")"
    elif v.tag == "native":
        return f"`{v.name}`"
    else:
        raise RuntimeError(v)


def render_value_as_source(v: Value):
    if v.tag == "str":
        return repr(v.value)
    else:
        return stringify_value(v)


def unwrap_stack(stack: Stack) -> Iterator[Value]:
    while stack is not None:
        x, stack = stack  # type: ignore
        yield x


def repr_stack(stack) -> List[Value]:
    return [*unwrap_stack(stack)][::-1]


def repr_scope(scope: Scope) -> Dict[str, Any]:
    d = dict(scope.values.items())
    if scope.parent is not None:
        d["(parent)"] = repr_scope(scope.parent)
    return d


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
