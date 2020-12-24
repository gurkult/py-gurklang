import gurklang.vm as vm
from gurklang.parser import parse
from gurklang.types import Int


def run(code):
    stack, _ = vm.run(parse(code))
    return stack


def nums(*args):
    stack = None
    for arg in args:
        stack = Int(arg), stack
    return stack


def test_dup():
    assert run('3 dup') == nums(3, 3)
    assert run('3 4 2dup') == nums(3, 4, 3, 4)


def test_drop():
    assert run('3 4 drop') == nums(3)
    assert run('3 4 2drop') == nums()


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


def test_rot_identities():
    assert run('3 4 5 rot rot') == run('3 4 5 unrot')
    assert run('3 4 5 rot rot rot') == run('3 4 5 unrot unrot unrot') == nums(3, 4, 5)
    assert run('3 4 5 rot unrot rot unrot') == nums(3, 4, 5)
