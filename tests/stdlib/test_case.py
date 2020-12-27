from pytest import raises

from tests.test_examples import run, number_stack


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
    { { (1)   { }
        (a n) { a n * n 1 - n! }
      } case
    } :n! jar
    1 6 n!
    """) == number_stack(720)


def test_case_does_not_recursion_error():
    assert run("""
    :math( * - ) import
    { { (1) { 11 }
        ()  { 1 - f }
      } case
    } :f jar
    1001 f
    """) == number_stack(11)


def test_case_parent_scope():
    assert run('10 { (a) {} parent-scope } parent-scope case a') == number_stack(10)


def test_case_ignore():
    assert run('1 2 3 4 5 {(_ _ .. . .) {}} case') == run("4 5 3")

    # 4 5 3

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


def test_case_stack_capture_order_in_tuple():
    assert run('(1 2 3 4) { ((. ... .. .)) {} } case') == run("1 4 3 2")
    assert run('(1 (2 (3 4) 5) 6) { ((. (.. (. .) ..) ..)) {} } case') == run("1 3 4 2 5 6")


def test_numbered_dot_pattern():
    assert (
        run('(1 2 3 4) { ((. .3 .2 .)) {} } case')
        == run('(1 2 3 4) { ((. ... .. .)) {} } case')
    )


def test_empty_stack_does_not_crash():
    assert (
        run('{ (.){1} (){2} } case')
        == run('2')
    )
