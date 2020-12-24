from .types import Scope, Stack, Value
from typing import Any, Iterator, List, Dict


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
        return f"{v.name} (built-in)"
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
