import pprint

from typing import Sequence, TypeVar, Tuple
from .. import parser
from .. import ast_parser
from ..vm_utils import render_value_as_source
from ..builtin_utils import BuiltinModule, Fail
from ..types import Atom, Box, Instruction, State, Str, Value, Stack, Scope, Int, Vec

from collections import deque


module = BuiltinModule("inspect")
T, V, S = Tuple, Value, Stack
Z = TypeVar("Z", bound=Stack)


@module.register_simple()
def tokenize(stack: T[V, S], fail: Fail):
    (source_code, rest) = stack
    if source_code.tag != "str":
        fail(f"{render_value_as_source(source_code)} is not a string")
    tokens = list(parser.lex_all(source_code.value))
    rv = Vec(())
    for token in reversed(tokens):
        begin, end = token.span
        tv = Vec((
            Atom(token.name.lower().replace("_", "-")),
            Str(token.value),
            Vec((Int(begin),
            Int(end)))
        ))
        rv = Vec((tv, rv))
    return (rv, rest)


def _ast_to_value(ast: ast_parser.ASTNode) -> Value:
    if isinstance(ast, ast_parser.IntLiteral):
        return Vec((Atom("int-literal"), Int(ast.value)))
    elif isinstance(ast, ast_parser.StrLiteral):
        return Vec((Atom("str-literal"), Str(ast.value)))
    elif isinstance(ast, ast_parser.AtomLiteral):
        return Vec((Atom("atom-literal"), Str(ast.value)))
    elif isinstance(ast, ast_parser.NameCall):
        return Vec((Atom("name"), Str(ast.value)))
    elif isinstance(ast, ast_parser.VecLiteral):
        rv = Vec(())
        for node in reversed(ast.nodes):
            rv = Vec((_ast_to_value(node), rv))
        return Vec((Atom("vec-literal"), rv))
    elif isinstance(ast, ast_parser.CodeLiteral):
        rv = Vec(())
        for node in reversed(ast.nodes):
            rv = Vec((_ast_to_value(node), rv))
        return Vec((Atom("code-literal"), rv))
    else:
        raise RuntimeError(ast)


@module.register_simple()
def build_ast(stack: T[V, S], fail: Fail):
    (source_code, rest) = stack
    if source_code.tag != "str":
        fail(f"{render_value_as_source(source_code)} is not a string")
    try:
        ast = ast_parser.parse_as_ast(source_code.value)
        return (_ast_to_value(ast), rest)
    except:
        return (Atom(":syntax-error"), rest)


@module.register_simple()
def code_dump(stack: T[V, S], fail: Fail):
    (code, rest) = stack
    if code.tag != "code":
        fail(f"{code} is not code")
    for i in code.instructions:
        print(render_value_as_source(i.as_vec()))
    return rest


@module.register()
def dis(state: State, fail: Fail):
    (head, rest) = state.infinite_stack()

    if head.tag == "atom":
        head = state.look_up_name_in_current_scope(head.value)

    if head.tag != "code":
        fail(f"{head} is not valid code or atom")

    last_id = 1

    tasks: "deque[tuple[int, Sequence[Instruction]]]" = deque([(last_id, head.instructions)])
    seen_code = {id(head.instructions): last_id}

    def get_code_id(instructions: Sequence[Instruction]):
        nonlocal last_id
        old_id = seen_code.get(id(instructions))
        if old_id is not None:
            return old_id
        last_id += 1
        tasks.append((last_id, instructions))
        return last_id

    while tasks:
        uid, instructions = tasks.popleft()
        seen_code[id(instructions)] = last_id
        print(f"Disassembling function {uid}:")

        for instruction in instructions:
            if instruction.tag == "put" and instruction.value.tag == "code":
                code_id = get_code_id(instruction.value.instructions)  # type: ignore
                print(f"(:Put [code #{code_id}])")

            elif instruction.tag == "put_code":
                code_id = get_code_id(instruction.instructions)
                print(f"(:PutCode [code #{code_id}])")

            else:
                print(render_value_as_source(instruction.as_vec()))
        print()

    return state.with_stack(rest)



@module.register_simple("type")
def get_type(stack: T[V, S], fail: Fail):
    (head, rest) = stack
    return (Atom(head.tag.replace("_", "-")), rest)


def _stack_to_vec(stack: Stack) -> Vec:
    if stack is None:
        return Vec(())
    else:
        head, rest = stack
        return Vec((head, _stack_to_vec(rest)))


@module.register_simple("box-id?")
def box_id(stack: T[V, S], fail: Fail):
    (box, rest) = stack
    if box.tag != "box":
        fail(f"{render_value_as_source(box)} is not a box")
    return (Int(box.id), rest)


@module.register("box-transactions?")
def box_transactions(state: State, fail: Fail):
    (box, rest) = state.infinite_stack()
    if box.tag != "box":
        fail(f"{render_value_as_source(box)} is not a box")
    return state.with_stack(rest).push(_stack_to_vec(state.read_box(box.id)))


@module.register("box-info!")
def box_info(state: State, fail: Fail):
    (box, rest) = state.infinite_stack()
    if box.tag != "box":
        fail(f"{render_value_as_source(box)} is not a box")
    print("Box id:", box.id)
    transaction_repr = render_value_as_source(_stack_to_vec(state.boxes[box.id]))
    print("Box transactions", transaction_repr)
    return state.with_stack(rest)


@module.register("box-exists?")
def does_box_exist(state: State, fail: Fail):
    (box, rest) = state.infinite_stack()
    if box.tag != "box":
        fail(f"{render_value_as_source(box)} is not a box")
    return state.with_stack(rest).push(Atom.bool(box.id in state.boxes))


@module.register_simple("make-box!")
def make_box(stack: T[V, S], fail: Fail):
    (id, rest) = stack
    if id.tag != "int":
        fail(f"{render_value_as_source(id)} is not an int")
    return (Box(id.value), rest)


@module.register("boxes?")
def __boxes(state: State, fail: Fail):
    # return a vector with pairs (id values) for boxes
    pairs = [
        (Int(id), _stack_to_vec(values))
        for (id, values) in state.boxes.items()
    ]
    pairs.sort(key=lambda pair: pair[0].value)
    return state.push(Vec([*map(Vec, pairs)]))


@module.register("boxes!")
def __boxes(state: State, fail: Fail):
    # print boxes state
    for id, values in state.boxes.items():
        vec = _stack_to_vec(values)
        print(f"{id: 2}", ":", render_value_as_source(vec))
    return state
