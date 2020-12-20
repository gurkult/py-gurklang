import pprint
from immutables import Map


_SCOPE_ID = 0
def generate_scope_id():
    global _SCOPE_ID
    _SCOPE_ID += 1
    return _SCOPE_ID


# print = lambda *_: None


def join_scopes(main_scope, closure_scope, indent=""):
    """
    Update the closure scope with the new changes
    """
    print = print_scope = lambda *_, **__: None
    print(indent + "join_scopes")
    if main_scope:
        print_scope(main_scope, indent+"    ")
    else:
        print(indent + "main_scope is None")
    if closure_scope:
        print_scope(closure_scope, indent+"    ")
    else:
        print(indent + "closure_scope is None")
    print(indent + "----------------\n")

    if main_scope is None:
        return closure_scope
    if closure_scope is None:
        return main_scope

    if main_scope["(id)"] == closure_scope["(id)"]:
        return main_scope

    else:
        result = closure_scope.set(
            "(parent)",
            join_scopes(main_scope, closure_scope["(parent)"], indent+"    ")
        )
        print("Result:")
        print_scope(result, indent+">>>> ")
        return result


def look_up_name(scope, name):
    if name in scope:
        return scope[name]
    elif scope["(parent)"]:
        return look_up_name(scope["(parent)"], name)
    else:
        raise KeyError(name)


def make_scope(parent):
    return Map({"(parent)": parent, "(id)": generate_scope_id()})


def call(stack, scope, function):
    tag, arg = function
    if tag == "native":
        new_stack, new_scope = arg(stack, scope)
        return new_stack, new_scope
    elif tag == "code":
        (instructions, closure) = arg
        if closure is None:
            local_scope = make_scope(scope)
        else:
            local_scope = make_scope(join_scopes(scope, closure))
        for instruction in instructions:
            stack, local_scope = execute(stack, local_scope, instruction)
        return stack, local_scope["(parent)"]
    else:
        raise RuntimeError(function)


def execute(stack, scope, instruction):
    tag, arg = instruction
    if tag == "put":
        return (arg, stack), scope
    elif tag == "put_code":
        return (("code", (arg, scope)), stack), scope
    elif tag == "call":
        fn = look_up_name(scope, arg)
        new_stack, new_scope = call(stack, scope, fn)
        return new_stack, new_scope
    else:
        raise RuntimeError(instruction)


def _str_value(v):
    tag, arg = v
    if tag == "str":
        return arg
    elif tag == "int":
        return str(arg)
    elif tag == "atom":
        return ":" + arg
    elif tag == "code":
        return "{...}"
    elif tag == "tuple":
        return "(" + ",".join(map(_str_value, arg)) + ")"
    elif tag == "native":
        return f"<builtin {arg.__name__}>"
    else:
        return "!!WTF!!"


def make_builtins():
    """
    Create the built-in scope populated with built-in functions
    """
    builtins_dict = {}

    def fail(name, reason, stack, scope):
        print(f"Failure in function {name!r}.")
        print("Reason:", reason)
        print("> Stack: ", repr_stack(stack))
        print("> Most inner scope: ", scope.delete("(parent)"))
        print("> Parent scope: ", scope["(parent)"].delete("(parent)"))
        raise RuntimeError(name, reason)

    def register(name=None):
        def inner(fn):
            fn_name = name or fn.__name__
            def new_fn(stack, scope):
                local_fail = lambda reason: fail(fn_name, reason, stack, scope)
                try:
                    return fn(stack, scope, local_fail)
                except Exception as e:
                    local_fail(f"uncaught exception {type(e)}: {' '.join(e.args)}")
            new_fn.__qualname__ = "new_fn"
            builtins_dict[name or fn.__name__] = ("native", new_fn)
        return inner

    ###

    @register()
    def dup(stack, scope, fail):
        (x, rest) = stack
        return (x, (x, rest)), scope

    @register()
    def swap(stack, scope, fail):
        (x, (y, rest)) = stack
        return (y, (x, rest)), scope

    @register()
    def rot3(stack, scope, fail):
        (z, (y, (x, rest))) = stack
        return (x, (y, (z, rest))), scope

    @register()
    def jar(stack, scope, fail):
        """
        Store a function by a name
        """
        (name_v, (code_v, rest)) = stack
        (name_tag, name) = name_v
        (code_tag, code) = code_v
        if name_tag != "atom":
            fail(f"{name_v} is not an atom")
        if code_tag not in ("code", "native"):
            fail(f"{code_v} is not code")
        return rest, scope.set(name, code_v)

    @register()
    def var(stack, scope, fail):
        """
        Store a value by a name
        """
        (name_v, (value, rest)) = stack
        (name_tag, name) = name_v
        if name_tag != "atom":
            fail(f"{name_v} is not an atom")
        fn = ("code", ([("put", value)], scope))
        return rest, scope.set(name, fn)

    @register()
    def print_string(stack, scope, fail):
        ([tag, arg], rest) = stack
        if tag != "str":
            fail(f"{(tag, arg)} is not a string")
        print(arg)
        return rest, scope

    @register("str")
    def str_(stack, scope, fail):
        (x, rest) = stack
        representation = ("str", _str_value(x))
        return (representation, rest), scope

    @register("+")
    def add(stack, scope, fail):
        ([xt, xv], ([yt, yv], rest)) = stack
        if xt != "int" or yt != "int":
            fail("not an integer")
        return (("int", xv + yv), rest), scope

    @register("!")
    def call_(stack, scope, fail):
        (function, rest) = stack
        return call(rest, scope, function)

    builtins_dict["print"] = ("code", ([("call", "str"), ("call", "print_string")], None))

    ###

    return Map(builtins_dict)


builtin_scope = make_builtins().set("(parent)", None).set("(id)", generate_scope_id())
global_scope = make_scope(parent=builtin_scope)



def unwrap_stack(stack):
    while stack is not None:
        x, stack = stack
        yield x


def repr_stack(stack):
    return [*unwrap_stack(stack)][::-1]


def repr_scope(scope):
    d = dict(scope.items())
    if d["(parent)"] is not None:
        d["(parent)"] = repr_scope(d["(parent)"])
    return d


def print_scope(scope, indent="", already_printed=Map()):
    if scope["(id)"] == builtin_scope["(id)"]:
        print(indent+"Builtin scope.")
        return

    # if scope["(id)"] == global_scope["(id)"]:
    #     print(indent+"Global scope.")
    #     return

    if scope["(id)"] in already_printed:
        print(indent + f"SCOPE #{scope['(id)']} (already printed)")
    else:
        print(indent + f"SCOPE #{scope['(id)']}")
        for key in scope:
            if key not in {"(id)", "(parent)"}:
                print(indent + f"{key} -> {_str_value(scope[key])}")
        if scope["(parent)"] is None:
            print(indent + "Root.")
        else:
            print(indent + "Parent:")
            print_scope(scope["(parent)"], indent+"    ", already_printed.set("(id)", 1))


def run(instructions):
    return call(
        stack=None,
        scope=global_scope,
        function=("code", (instructions, None))
    )