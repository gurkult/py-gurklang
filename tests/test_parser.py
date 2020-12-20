import re
from gurklang.parser_utils import build_regexp


def test_build_regexp():
    assert build_regexp([
        ("foo", "bar"),
        ("fizz", "buzz"),
    ], re.I | re.M) == re.compile("(?P<foo>bar)|(?P<fizz>buzz)", re.I | re.M)
