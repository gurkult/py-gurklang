import gurklang.vm as vm
from gurklang.parser import parse
from gurklang.types import Int


def run(code):
    stack = vm.run(parse(code)).stack
    return stack


def number_stack(*args):
    stack = None
    for arg in args:
        stack = Int(arg), stack
    return stack


def test_factorial():
    assert run(R"""
    :math (* -) import
    { { (. .) { dup 1 - rot * swap n! }
        (1) {}
      } case
    } :n! jar
    1 10 n!
    """) == number_stack(3628800)


def test_generators(capsys):
    run(R"""
    :math ( +       ) import
    :coro ( iterate ) import

    { dup println 1 + } (1 ())
    iterate
    iterate
    iterate
    iterate
    """)
    assert capsys.readouterr().out == '1\n2\n3\n4\n'


def test_higher_order_functions(capsys):
    run(R"""
    :math ( + ) import
    :inspect ( code-dump ) import

    { :f var :x var { x f ! } } :my-close jar

    { { + } my-close } :make-adder jar

    5 make-adder :add5 jar

    37 add5 println  #=> 42
    40 add5 println  #=> 45
    """)
    assert capsys.readouterr().out == '42\n45\n'
