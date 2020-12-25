import re
from gurklang.parser_utils import build_regexp
from gurklang.parser import parse
from hypothesis import given, infer, assume


@given(program=infer)
def test_any_program_without_parens_brackets_and_colons_is_valid(program: str):
    assume(set(program) & {"(", ")", "{", "}", ":"} == set())
    parse(program)


def test_build_regexp():
    assert build_regexp([
        ("foo", "bar"),
        ("fizz", "buzz"),
    ], re.I | re.M) == re.compile("(?P<foo>bar)|(?P<fizz>buzz)", re.I | re.M)
