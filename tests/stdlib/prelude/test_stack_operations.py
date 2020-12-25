from gurklang.types import CallByName, Put, Value
from hypothesis import infer, given
from tests.test_examples import run, irun, number_stack as nums


@given(a=infer)
def test_dup(a: int):
    assert run(f'{a} dup') == nums(a, a)


@given(a=infer)
def test_dup_value(a: Value):
    assert irun(Put(a), CallByName("dup")) == (a, (a, None))


@given(a=infer, b=infer)
def test_2dup(a: int, b: int):
    assert run(f'{a} {b} 2dup') == nums(a, b, a, b)


@given(a=infer, b=infer)
def test_drop(a: int, b: int):
    assert run(f'{a} {b} drop') == nums(a)


@given(a=infer, b=infer, c=infer)
def test_2drop(a: int, b: int, c: int):
    assert run(f'{a} {b} {c} 2drop') == nums(a)


def test_swap():
    assert run('3 4 swap') == nums(4, 3)
    assert run('3 4 5 6 2swap') == nums(5, 6, 3, 4)


def test_over():
    assert run('3 4 over') == nums(3, 4, 3)
    assert run('3 4 5 6 2over') == nums(3, 4, 5, 6, 3, 4)


def test_rot():
    assert run('3 4 5 rot') == nums(5, 3, 4)
    assert run('3 4 5 6 7 8 2rot') == nums(7, 8, 3, 4, 5, 6)


def test_unrot():
    assert run('3 4 5 unrot') == nums(4, 5, 3)
    assert run('3 4 5 6 7 8 2unrot') == nums(5, 6, 7, 8, 3, 4)


@given(a=infer, b=infer, c=infer)
def test__rot_rot__is__unrot(a: int, b: int, c: int):
    assert run('3 4 5 rot rot') == run('3 4 5 unrot')

@given(a=infer, b=infer, c=infer)
def test__rot_rot_rot__is__id(a: int, b: int, c: int):
    assert run(f'{a} {b} {c} rot rot rot') == nums(a, b, c)

@given(a=infer, b=infer, c=infer)
def test__unrot_unrot_unrot__is__id(a: int, b: int, c: int):
    assert run(f'{a} {b} {c} unrot unrot unrot') == nums(a, b, c)
