from typing import Iterator
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


def _parse_vec(token_stream: Iterator[Token]) -> Iterator[Instruction]:
    n = 0
    for token in token_stream:
        if token.name == "RPAR":
            break

        if token.name == "INT":
            yield Put(Int(int(token.value)))
        elif token.name == "NAME":
            yield Put(Atom(token.value))
        elif token.name == "STR_D" or token.name == "STR_S":
            yield Put(Str(ast.literal_eval(token.value)))
        elif token.name == "LBR":
            yield PutCode(list(_parse_codeblock(token_stream)))
        else:
            raise ValueError(token)

        n += 1
    else:
        raise ValueError(token)  # type: ignore
    yield MakeVec(n)


def _parse_codeblock(token_stream: Iterator[Token]) -> Iterator[Instruction]:
    for token in token_stream:
        if token.name == "RBR":
            break

        elif token.name == "LBR":
            # put_code is distinct from put, because the runtime
            # will attach a closure to the code
            yield PutCode(list(_parse_codeblock(token_stream)))

        elif token.name == "LPAR":
            yield from _parse_vec(token_stream)

        elif token.name == "INT":
            yield Put(Int(int(token.value)))

        elif token.name == "NAME":
            yield CallByName(token.value)

        elif token.name == "ATOM":
            yield Put(Atom(token.value[1:]))

        elif token.name == "STR_D" or token.name == "STR_S":
            yield Put(Str(ast.literal_eval(token.value)))

        else:
            raise ValueError(token)
    else:
        raise ValueError(token)  # type: ignore


def _parse_stream(token_stream: Iterator[Token], length: int) -> Iterator[Instruction]:
    return _parse_codeblock(itertools.chain(
        token_stream,
        [Token("RBR", "}", length)],
    ))


def parse(source: str) -> list[Instruction]:
    return list(_parse_stream(_lex(source), len(source)))
