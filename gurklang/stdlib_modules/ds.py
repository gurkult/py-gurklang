from typing import Tuple

from immutables import Map

from ..vm_utils import render_value_as_source
from ..builtin_utils import BuiltinModule, Fail, make_function
from ..types import Atom, NativeFunction, State, Value, Stack


module = BuiltinModule("ds")
Hamt = Map[Value, Value]

def make_hamt(native_hamt: Hamt) -> NativeFunction:
    @make_function("--hamt")
    def _hamt(state: State, fail: Fail, *, _native_hamt: Hamt=native_hamt) -> State:
        (cmd, rest) = state.infinite_stack()

        if cmd.tag != "atom":
            fail(f"{render_value_as_source(cmd)} is not an atom")

        if cmd is Atom("get"):
            (key, rest2) = rest
            value = _native_hamt.get(key)
            if value is None:
                return state.with_stack(rest2).push(Atom("nil"))
            else:
                return state.with_stack(rest2).push(value)

        elif cmd is Atom("set"):
            (value, (key, rest2)) = rest
            return state.with_stack(rest2).push(make_hamt(_native_hamt.set(key, value)))

        elif cmd is Atom("del"):
            (key, rest2) = rest
            if key not in _native_hamt:
                return state.with_stack(rest2).push(_hamt)
            return state.with_stack(rest2).push(make_hamt(_native_hamt.delete(key)))

        else:
            fail(f"Unknown method :{cmd.value}")
    return _hamt


@module.register_simple()
def hamt(stack: Stack, _fail: Fail) -> Stack:
    return (make_hamt(Map()), stack)
