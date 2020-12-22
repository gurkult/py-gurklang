import gurklang.vm as vm
from gurklang.parser import parse
from gurklang.types import Int


def run(code):
    stack, _ = vm.run(parse(code))
    return stack


def number_stack(*args):
    stack = None
    for arg in args:
        stack = Int(arg), stack
    return stack


def test_case_value_match():
    assert run('1 { (1) {4} } case') == number_stack(4)


def test_case_multiple_value_match():
    assert run('1 3 8 { (1 3 8) {4} } case') == number_stack(4)


def test_case_multiple_patterns():
    assert run("""
    1 2 3
    { (1 2 4) {1}
      (1 2 3) {2}
      (1 2 2) {3}
    } case
    """) == number_stack(2)


def test_case_simple_stack_capture():
    assert run(':math (+) import 1 { (.) {1 +} } case') == number_stack(2)


def test_case_stack_capture_order():
    assert run('1 2 3 4 { (. ... .. .) {} } case') == number_stack(1, 4, 3, 2)


def test_case_named_capture():
    assert run('1 {(a) {a}} case') == number_stack(1)


def test_case_atom_match():
    assert run(':rect {(:rect) {4}} case') == number_stack(4)


def test_case_tuple_match():
    """impossible until the parser allows nested tuples"""
    assert True
