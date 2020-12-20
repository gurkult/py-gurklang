import ast
import itertools
import re


TOKEN_RE = re.compile(r"""
  (?P<COMMENT> \#.*$                 )
| (?P<LPAR>    \(                    )
| (?P<RPAR>    \)                    )
| (?P<LBR>     \{                    )
| (?P<RBR>     \}                    )
| (?P<INT>     \d+                   )
| (?P<STR_D>   "(?:\\.|[^"])+"       )
| (?P<STR_S>   '(?:\\.|[^'])+'       )
| (?P<ATOM>    \:[-+*^=?!_a-zA-Z0-9]+)
| (?P<NAME>    [-+*^=?!_a-zA-Z0-9]+  )
""", re.M | re.X)


# _ATOM_CACHE = {}
# _ATOM_ID = 1

# def atom_id(atom: str):
#     global _ATOM_ID
#     if atom not in _ATOM_CACHE:
#         _ATOM_CACHE[atom] = _ATOM_ID
#         _ATOM_ID += 1
#     return _ATOM_CACHE[atom]


def _lex(source: str):
    for m in TOKEN_RE.finditer(source):
        name, value = next(
            (name, value) for (name, value) in m.groupdict().items()
            if value is not None
        )
        if name != "COMMENT":
            yield (name, value, m.start())


def _parse_tuple(token_stream):
    values = []

    for name, value, pos in token_stream:
        if name == "RPAR":
            break

        if name not in ("NAME", "INT", "STR_D", "STR_S"):
            raise ValueError((name, value, pos))

        if name == "INT":
            values.append(("int", int(value)))
        elif name == "NAME":
            values.append(("atom", value))
        else:
            values.append(("str", ast.literal_eval(value)))
    else:
        raise ValueError((name, value, pos))

    return ("tuple", values)


def _parse_codeblock(token_stream) -> list:
    instructions = []
    for name, value, pos in token_stream:
        if name == "RBR":
            break
        elif name == "LBR":
            instr = ("put_code",_parse_codeblock(token_stream))
        elif name == "LPAR":
            instr = ("put", _parse_tuple(token_stream))
        elif name == "INT":
            instr = ("put", ("int", int(value)))
        elif name == "NAME":
            instr =("call", value)
        elif name == "ATOM":
            instr = ("put", ("atom", value[1:]))
        elif name in ("STR_D", "STR_S"):
            instr = ("put", ("str", ast.literal_eval(value)))
        else:
            raise ValueError((name, value, pos))
        instructions.append(instr)
    else:
        raise ValueError((name, value, pos))
    return instructions


def _parse_stream(token_stream, length):
    return _parse_codeblock(itertools.chain(
        token_stream,
        [("RBR", "}", length)],
    ))


def parse(source: str):
    return _parse_stream(_lex(source), len(source))
