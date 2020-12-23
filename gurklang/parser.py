from typing import Any, Iterator, List, Generator, Tuple
from gurklang.parser_utils import build_tokenizer
from gurklang.types import Instruction, Put, PutCode, CallByName, MakeVec, Atom, Str, Int
import ast
import itertools



tokenizer = build_tokenizer(
    (
        ("LPAR", r"\("),
        ("RPAR", r"\)"),
        ("LBR", r"\{"),
        ("RBR", r"\}"),
        ("INT", r"[+-]\d+"),
        ("STR_D", r'"(?:\\.|[^"])+"'),
        ("STR_S", r"'(?:\\.|[^'])+'"),
        ("ATOM", r"\:[^\"'(){}# \n\t]+"),
        ("NAME", r"[^\"'(){}# \n\t]+"),
    ),
    ignored_tokens=(
        ("COMMENT", r"\#.*($|\n)"),
        ("WHITESPACE", r"\s+"),
    ),
    middleware={
        "NAME": lambda s: ("INT", s) if s.isascii() and s.isdigit() else ("NAME", s)
    }
)


Token = tokenizer.token_type


def _lex(source: str) -> Iterator[Token]:
    return tokenizer.tokenize(source)


def _parse_vec(source: str, token_stream: Iterator[Token]) -> Iterator[Instruction]:
    n = 0
    for token in token_stream:
        if token.name == "RPAR":
            break

        if token.name == "INT":
            yield Put(Int(int(token.value)))
        elif token.name == "NAME":
            yield Put(Atom.make(token.value))
        elif token.name == "ATOM":
            yield Put(Atom.make(":" + token.value))
        elif token.name == "LPAR":
            yield from _parse_vec(source, token_stream)
        elif token.name in ["STR_D", "STR_S"]:
            yield Put(Str(ast.literal_eval(token.value)))
        elif token.name == "LBR":
            yield PutCode(list(_parse_codeblock(source, token_stream)))
        else:
            raise ValueError(token)

        n += 1
    else:
        raise ValueError(token)  # type: ignore
    yield MakeVec(n)


def _collect(gen):
    rv: Any = None
    def helper_generator():
        nonlocal rv
        rv = yield from gen
    elements = list(helper_generator())
    return (rv, elements)


def _parse_codeblock(
    source: str,
    token_stream: Iterator[Token]
) -> Generator[Instruction, None, Tuple[int, int]]:
    for token in token_stream:
        if token.name == "RBR":
            return token.span

        elif token.name == "LBR":
            # put_code is distinct from put, because the runtime
            # will attach a closure to the code

            (_, end_pos), elements = _collect(_parse_codeblock(source, token_stream))

            yield PutCode(elements, source_code=source[token.position:end_pos])

        elif token.name == "LPAR":
            yield from _parse_vec(source, token_stream)

        elif token.name == "INT":
            yield Put(Int(int(token.value)))

        elif token.name == "NAME":
            yield CallByName(token.value)

        elif token.name == "ATOM":
            yield Put(Atom.make(token.value[1:]))

        elif token.name in ["STR_D", "STR_S"]:
            yield Put(Str(ast.literal_eval(token.value)))

        else:
            raise ValueError(token)
    else:
        raise ValueError(token)  # type: ignore


def _parse_stream(source: str, token_stream: Iterator[Token]) -> Iterator[Instruction]:
    return _parse_codeblock(source, itertools.chain(
        token_stream,
        [Token("RBR", "}", len(source))],
    ))


def parse(source: str) -> List[Instruction]:
    return list(_parse_stream(source, _lex(source)))
