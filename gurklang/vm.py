from immutables import Map
from typing import Any, Callable, Iterator, NoReturn, Optional, TypeVar
from gurklang.types import Atom, Call, Int, NativeFunction, Put, Scope, Stack, Str, Value, Instruction, Code


_SCOPE_ID = 0
def generate_scope_id():
    global _SCOPE_ID
    _SCOPE_ID += 1
    return _SCOPE_ID


def make_scope(parent: Optional[Scope]) -> Scope:
    return Scope(parent, generate_scope_id(), Map())


def call(stack: Stack, scope: Scope, function: Value) -> tuple[Stack, Scope]:
    if function.tag == "native":
        return function.fn(stack, scope)

    elif function.tag == "code":
        local_scope = make_scope(parent=scope.join_closure_scope(function.closure))

        for instruction in function.instructions:
            stack, local_scope = execute(stack, local_scope, instruction)

        assert local_scope.parent is not None
        return stack, local_scope.parent

    else:
        raise RuntimeError(function)


def execute(stack: Stack, scope: Scope, instruction: Instruction) -> tuple[Stack, Scope]:
    if instruction.tag == "put":
        return (instruction.value, stack), scope

    elif instruction.tag == "put_code":
        return (Code(instruction.value, scope), stack), scope

    elif instruction.tag == "call":
        return call(stack, scope, scope[instruction.function_name])

    else:
        raise RuntimeError(instruction)


def _stringify_value(v: Value):
    if v.tag == "str":
        return v.value
    elif v.tag == "int":
        return str(v.value)
    elif v.tag == "atom":
        return ":" + v.value
    elif v.tag == "code":
        return "{...}"
    elif v.tag == "vec":
        return "(" + ",".join(map(_stringify_value, v.values)) + ")"
    elif v.tag == "native":
        return f"<builtin {v.fn.__name__}>"
    else:
        raise RuntimeError(v)


def make_builtins(scope_id: int):
    """
    Create the built-in scope populated with built-in functions
    """
    builtins_dict = {}

    def fail(name: str, reason: str, stack: Stack, scope: Scope):
        print(f"Failure in function {name!r}.")
        print("Reason:", reason)
        print("> Stack: ", repr_stack(stack))
        print("> Most inner scope: ", scope.values)
        if scope.parent is not None:
            print("> Parent scope: ", scope.parent.values)
        raise RuntimeError(name, reason)

    Fail = Callable[[str], NoReturn]

    # Z is contravariant because a function should accept a subset of
    # stacks (e.g. only stacks with at least 2 elements)
    Z = TypeVar("Z", bound=Stack, contravariant=True)

    def register(name: Optional[str] = None):
        def inner(fn: Callable[[Z, Scope, Fail], tuple[Stack, Scope]]):
            fn_name = name or fn.__name__
            def new_fn(stack, scope):
                local_fail: Fail = lambda reason: fail(fn_name, reason, stack, scope)
                try:
                    return fn(stack, scope, local_fail)
                except Exception as e:
                    local_fail(f"uncaught exception {type(e)}: {' '.join(e.args)}")
            new_fn.__qualname__ = "new_fn"
            builtins_dict[name or fn.__name__] = NativeFunction(new_fn)
        return inner

    ###

    # Shortcuts for brevity
    T, V, S = tuple, Value, Stack

    @register()
    def dup(stack: T[V, S], scope: Scope, fail: Fail):
        (x, rest) = stack
        return (x, (x, rest)), scope

    @register()
    def swap(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
        (x, (y, rest)) = stack
        return (y, (x, rest)), scope

    @register()
    def rot3(stack: T[V, T[V, T[V, S]]], scope: Scope, fail: Fail):
        (z, (y, (x, rest))) = stack
        return (x, (y, (z, rest))), scope

    @register()
    def jar(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
        """
        Store a function by a name
        """
        (identifier, (code, rest)) = stack
        if identifier.tag != "atom":
            fail(f"{identifier} is not an atom")
        if code.tag != "code" and code.tag != "native":
            fail(f"{code} is not code")
        return rest, scope.with_member(identifier.value, code)

    @register()
    def var(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
        """
        Store a value by a name
        """
        (identifier, (value, rest)) = stack
        if identifier.tag != "atom":
            fail(f"{identifier} is not an atom")
        fn = Code([Put(value)], closure=scope)
        return rest, scope.with_member(identifier.value, fn)

    @register()
    def print_string(stack: T[V, S], scope: Scope, fail: Fail):
        (head, rest) = stack
        if head.tag != "str":
            fail(f"{head} is not a string")
        print(head.value)
        return rest, scope

    @register("str")
    def str_(stack: T[V, S], scope: Scope, fail: Fail):
        (x, rest) = stack
        representation = Str(_stringify_value(x))
        return (representation, rest), scope

    @register("+")
    def add(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
        (x, (y, rest)) = stack
        if x.tag != "int" or y.tag != "int":
            fail(f"{x} cannot be added with {y}")
        return (Int(x.value + y.value), rest), scope

    @register("!")
    def exclamation_mark(stack: T[V, S], scope: Scope, fail: Fail):
        (function, rest) = stack
        return call(rest, scope, function)

    @register("if")
    def if_(stack: T[V, T[V, T[V, S]]], scope: Scope, fail: Fail):
        (condition, (else_, (then, rest))) = stack
        if condition == Atom("true"):
            return call(rest, scope, then)
        elif condition == Atom("false"):
            return call(rest, scope, else_)
        else:
            fail(f"{condition} is not a boolean (:true/:false)")

    builtins_dict["print"] = Code([Call("str"), Call("print_string")], closure=None)

    ###
    return Scope(parent=None, id=scope_id, values=Map(builtins_dict))


builtin_scope = make_builtins(generate_scope_id())
global_scope = make_scope(parent=builtin_scope)



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


def run(instructions):
    return call(
        stack=None,
        scope=global_scope,
        function=Code(instructions, closure=None)
    )
