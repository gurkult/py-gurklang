"""
Alternative parser that produces an AST instead of a sequencence of instructions.
"""
from __future__ import annotations
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Callable, Iterator, List, Optional, Sequence, Tuple, Type, Union
from ast import literal_eval
from . import parser

@dataclass(frozen=True)
class IntLiteral:
    value: int

@dataclass(frozen=True)
class AtomLiteral:
    value: str

@dataclass(frozen=True)
class StrLiteral:
    value: str

@dataclass(frozen=True)
class NameCall:
    value: str

@dataclass(frozen=True)
class VecLiteral:
    nodes: List[ASTNode]

@dataclass(frozen=True)
class CodeLiteral:
    nodes: List[ASTNode]


ASTNode = Union[IntLiteral, AtomLiteral, StrLiteral, VecLiteral, NameCall, CodeLiteral]


def parse_as_ast(source: str) -> CodeLiteral:
    parser.parse(source)  # throw a nice syntax error

    stream = parser.lex(source)
    stream.push(parser.Token("RIGHT_BRACE", ")", len(source)))

    return _parse_code_literal(stream)


def _parse_code_literal(stream: parser.Stream) -> CodeLiteral:
    nodes: List[ASTNode] = []
    for token in stream:
        if token.name == "LEFT_PAREN":
            nodes.append(_parse_vec(stream))
        elif token.name == "INT":
            nodes.append(IntLiteral(int(token.value)))
        elif token.name == "STRING":
            nodes.append(StrLiteral(literal_eval(token.value)))
        elif token.name == "ATOM":
            nodes.append(AtomLiteral(token.value[1:]))
        elif token.name == "NAME":
            nodes.append(NameCall(token.value))
        elif token.name == "LEFT_BRACE":
            nodes.append(_parse_code_literal(stream))
        elif token.name == "RIGHT_BRACE":
            break
        else:
            assert False
    return CodeLiteral(nodes)


def _parse_vec(stream: parser.Stream) -> VecLiteral:
    nodes: List[ASTNode] = []
    for token in stream:
        if token.name == "LEFT_PAREN":
            nodes.append(_parse_vec(stream))
        elif token.name == "INT":
            nodes.append(IntLiteral(int(token.value)))
        elif token.name == "STRING":
            nodes.append(StrLiteral(literal_eval(token.value)))
        elif token.name == "ATOM":
            nodes.append(AtomLiteral(token.value))
        elif token.name == "NAME":
            nodes.append(AtomLiteral(token.value))
        elif token.name == "LEFT_BRACE":
            nodes.append(_parse_code_literal(stream))
        elif token.name == "RIGHT_PAREN":
            break
        else:
            assert False
    return VecLiteral(nodes)


###################
#    Searching    #
###################

def make_pattern_exact(node1: ASTNode) -> ASTSinglePattern:
    def pattern(node2: ASTNode):
        return node1 == node2
    return pattern

def make_pattern_of_types(*ts: Type[ASTNode]) -> ASTSinglePattern:
    def pattern(node: ASTNode):
        return isinstance(node, ts)  # type: ignore
    return pattern

def pattern_any(node: ASTNode):
    return True

def pattern_none(node: ASTNode):
    return False

def make_pattern_anyvec(subpattern: ASTSinglePattern = pattern_any):
    def pattern(node: ASTNode):
        return isinstance(node, VecLiteral) and all(map(subpattern, node.nodes))
    return pattern

def make_pattern_anycode(subpattern: ASTSinglePattern = pattern_any):
    def pattern(node: ASTNode):
        return isinstance(node, CodeLiteral) and all(map(subpattern, node.nodes))
    return pattern

def make_exact_pattern_vec(*subpatterns: ASTSinglePattern) -> ASTSinglePattern:
    def pattern(node: ASTNode):
        return (
            isinstance(node, VecLiteral)
            and len(node.nodes) == len(subpatterns)
            and all(p(n) for p, n in zip(subpatterns, node.nodes))
        )
    return pattern

def make_exact_pattern_code(*subpatterns: ASTSinglePattern) -> ASTSinglePattern:
    def pattern(node: ASTNode):
        return (
            isinstance(node, CodeLiteral)
            and len(node.nodes) == len(subpatterns)
            and all(p(n) for p, n in zip(subpatterns, node.nodes))
        )
    return pattern

def pattern_union(*patterns: ASTSinglePattern) -> ASTSinglePattern:
    def pattern(node: ASTNode):
        return any(p(node) for p in patterns)
    return pattern

def pattern_intersection(*patterns: ASTSinglePattern) -> ASTSinglePattern:
    def pattern(node: ASTNode):
        return all(p(node) for p in patterns)
    return pattern

ASTSinglePattern = Callable[[ASTNode], bool]


def find(*patterns: ASTSinglePattern):
    def _find(nodes: Sequence[ASTNode]) -> Iterator[Sequence[ASTNode]]:
        for i in range(len(nodes) - len(patterns)):
            slice_ = nodes[i:i+len(patterns)]
            if all(p(n) for p, n in zip(patterns, slice_)):
                yield slice_
    return _find


eq = make_pattern_exact
oft = make_pattern_of_types
t_int = oft(IntLiteral)
t_vec = oft(VecLiteral)
t_code = oft(CodeLiteral)
t_str = oft(StrLiteral)
t_name = oft(NameCall)
t_atom = oft(AtomLiteral)
t_any = pattern_any
t_none = pattern_none
por = pattern_union
pand = pattern_intersection
avec = make_pattern_anyvec
acode = make_pattern_anycode
xvec = make_exact_pattern_vec
xcode = make_exact_pattern_code

__all__ = (
    "find",

    "eq",
    "oft",
    "t_int",
    "t_vec",
    "t_code",
    "t_str",
    "t_name",
    "t_atom",
    "t_any",
    "t_none",
    "por",
    "pand",
    "avec",
    "acode",
    "xvec",
    "xcode",
)
