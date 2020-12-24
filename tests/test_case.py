from pytest import raises

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


def test_case_in_recursive_function():
    assert run("""
    :math( * - ) import
    { { (a n) { a n * n 1 - n! }
        (1) {}
      } case
    } :n! jar
    1 6 n!
    """) == number_stack(720)


def test_case_does_not_recursion_error():
    assert run("""
    :math( * - ) import
    { { () { 1 - f }
        (1) {11}
      } case
    } :f jar
    3000 f
    """) == number_stack(11)


def test_case_parent_scope():
    assert run('10 { (a) {} parent-scope } parent-scope case a') == number_stack(10)


def test_case_ignore():
    assert run('1 2 3 4 5 {(_ _ .. . .) {}}case') == number_stack(4, 5, 3)


def test_case_ignore_does_not_bind():
    with raises(KeyError):
        run('1 {(_) {}} case _')


def test_case_no_leak_of_variables():
    with raises(KeyError):
        run('10 { (a) {}} case a')


def test_case_atom_match():
    assert run(' :rect {(:rect) {4}} case') == number_stack(4)


def test_case_tuple_match():
    assert run(':math (*) import (rect 10 10) {((:rect . .)) { * } } case') == number_stack(100)
