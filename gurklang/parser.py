from typing import Any, Iterator, List, Literal, NamedTuple, Union
from gurklang.types import (
    Instruction,
    Put, PutCode, Call,

    Value,
    Atom, Str, Int, Vec, Code, NativeFunction
)
import ast
import itertools
import re


TOKEN_RE = re.compile(r"""
  (?P<COMMENT> \#.*$                     )
| (?P<LPAR>    \(                        )
| (?P<RPAR>    \)                        )
| (?P<LBR>     \{                        )
| (?P<RBR>     \}                        )
| (?P<INT>     [-+]?(?:0|[1-9]\d*        )
| (?P<STR_D>   "(?:\\.|[^"])+"           )
| (?P<STR_S>   '(?:\\.|[^'])+'           )
| (?P<ATOM>    \:(?!\d)[^"'(){}#: \n\t]+ )
| (?P<NAME>    (?!\d)[^"'(){}#: \n\t]+   )
""", re.M | re.X)


class Token(NamedTuple):
    name: Literal["COMMENT", "LPAR", "RPAR", "LBR", "RBR", "INT", "STR_D", "STR_S", "ATOM", "NAME"]
    value: str
    position: int


def _lex(source: str) -> Iterator[Token]:
    for m in TOKEN_RE.finditer(source):
        name, value = next(
            (name, value) for (name, value) in m.groupdict().items()
            if value is not None
        )
        if name != "COMMENT":
            yield Token(name, value, m.start())  # type: ignore


def _parse_vec_inner(token_stream: Iterator[Token]) -> Iterator[Value]:
    for token in token_stream:
        if token.name == "RPAR":
            break

        if token.name not in ("NAME", "INT", "STR_D", "STR_S"):
            raise ValueError(token)

        if token.name == "INT":
            yield Int(int(token.value))
        elif token.name == "NAME":
            yield Atom(token.value)
        else:
            yield Str(ast.literal_eval(token.value))
    else:
        raise ValueError(token)  # type: ignore


def _parse_vec(token_stream: Iterator[Token]) -> Vec:
    return Vec(list(_parse_vec_inner(token_stream)))


def _parse_codeblock(token_stream: Iterator[Token]) -> Iterator[Instruction]:
    for token in token_stream:
        if token.name == "RBR":
            break

        elif token.name == "LBR":
            # put_code is distinct from put, because the runtime
            # will attach a closure to the code
            yield PutCode(list(_parse_codeblock(token_stream)))

        elif token.name == "LPAR":
            yield Put(_parse_vec(token_stream))

        elif token.name == "INT":
            yield Put(Int(int(token.value)))

        elif token.name == "NAME":
            yield Call(token.value)

        elif token.name == "ATOM":
            yield Put(Atom(token.value[1:]))

        elif token.name in ("STR_D", "STR_S"):
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
