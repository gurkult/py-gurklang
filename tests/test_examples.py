from pytest import raises
import time
import gurklang.vm as vm
from gurklang.parser import parse
from gurklang.types import Instruction, Int


def run(code):
    return irun(*parse(code))


def irun(*instructions: Instruction):
    start_time = time.time()
    def on_timeout_bail(*_):
        if time.time() >= start_time + 1:
            raise TimeoutError
    return vm.run_with_middleware(instructions, on_timeout_bail).stack


# Meta-test:
def test_run_should_catch_infinite_loop():
    with raises(TimeoutError):
        run("{ (1 5) sleep dup ! } dup ! ")


def number_stack(*args):
    stack = None
    for arg in args:
        stack = Int(arg), stack
    return stack


def test_factorial():
    assert run(R"""
    :math (* -) import
    { { (1) {}
        (. .) { dup 1 - rot * swap n! }
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
