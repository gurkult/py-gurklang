from .types import Scope, Stack, Value
from typing import Any, Iterator


def stringify_value(v: Value):
    if v.tag == "str":
        return v.value
    elif v.tag == "int":
        return str(v.value)
    elif v.tag == "atom":
        return ":" + v.value
    elif v.tag == "code":
        return "{...}"
    elif v.tag == "vec":
        return "(" + " ".join(map(stringify_value, v.values)) + ")"
    elif v.tag == "native":
        return f"<builtin {v.fn.__name__}>"
    else:
        raise RuntimeError(v)


def unwrap_stack(stack: Stack) -> Iterator[Value]:
    while stack is not None:
        x, stack = stack  # type: ignore
        yield x


def repr_stack(stack) -> list[Value]:
    return [*unwrap_stack(stack)][::-1]


def repr_scope(scope: Scope) -> dict[str, Any]:
    d = dict(scope.values.items())
    if scope.parent is not None:
        d["(parent)"] = repr_scope(scope.parent)
    return d
