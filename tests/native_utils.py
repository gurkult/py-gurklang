from functools import wraps
from textwrap import dedent
from gurklang.vm import run
from gurklang.parser import parse
from gurklang.types import Int, Str, Vec

from hypothesis import given, infer
from hypothesis.strategies import composite, integers, text, lists, SearchStrategy
from gurklang.types import Atom, Put, Value
from typing import Callable, Union, Type


_prelude = parse("""
{
    {
        (:true :true) { :true  }
        (_     _    ) { :false }
    } case
} :&& jar

{
    {
        (:false :false) { :false  }
        (_      _     ) { :true   }
    } case
} :|| jar
""")


def _run_test(*xs: Value, code: str, name: str):
    state = run(_prelude + [Put(x) for x in xs] + parse(code))  # type: ignore
    assert state.stack is not None, name
    (head, _) = state.stack
    assert head == Atom("true"), name


def forall(*types: Union[Type[Value], SearchStrategy]):
    def decorator(fn: Callable[[Callable[[str], None]], None]):
        code = fn.__doc__
        name = fn.__name__

        var_names = [f"arg{i}" for i in range(len(types))]
        var_list = ", ".join(var_names)
        exec(dedent(f"""
            def _last_test({var_list}):
                _run_test({var_list}, code={code!r}, name={name!r})
        """), globals())
        global _last_test
        _last_test = wraps(fn)(_last_test)  # type: ignore
        _last_test.__annotations__ = {v: vt for (v, vt) in zip(var_names, types)}  # type: ignore
        _last_test = given(**{
            v: vt if isinstance(vt, SearchStrategy) else infer
            for (v, vt) in zip(var_names, types)})(_last_test)  # type: ignore
        return _last_test  # type: ignore
    return decorator


@composite
def atoms(draw):
    return draw(text("abcdefghijklmonqpstuvwxyz0123456789-=<>!?", min_size=1, max_size=16))


@composite
def comparables(draw):
    """
    Strategy for producing a pair of values that are valid for comparison with =
    """
    choice = draw(integers(0, 2))
    if choice == 0:
        return Vec([Int(draw(integers())), Int(draw(integers()))])
    elif choice == 1:
        return Vec([Str("".join(draw(text()))), Str("".join(draw(text())))])
    else:
        xys = draw(lists(comparables()))  # type: ignore
        xs = [v.values[0] for v in xys]
        ys = [v.values[1] for v in xys]
        return Vec([Vec(xs), Vec(ys)])
