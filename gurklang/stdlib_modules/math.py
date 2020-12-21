import math

from typing import TypeVar
from ..builtin_utils import Module, Fail
from ..types import Value, Stack, Scope, Int, Vec, Atom


module = Module("math")
T, V, S = tuple, Value, Stack
Z = TypeVar("Z", bound=Stack)


@module.register("<")
def add(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (y, (x, rest)) = stack
    if x.tag != "int" or y.tag != "int":
        fail(f"{x} cannot be compared with {y}")
    return ([Atom("false"), Atom("true")][x.value < y.value], rest), scope


@module.register("+")
def add(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (y, (x, rest)) = stack
    if x.tag != "int" or y.tag != "int":
        fail(f"{x} cannot be added with {y}")
    return (Int(x.value + y.value), rest), scope


@module.register("-")
def add(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (y, (x, rest)) = stack
    if x.tag != "int" or y.tag != "int":
        fail(f"{y} cannot be subtracted from {x}")
    return (Int(x.value - y.value), rest), scope


@module.register("*")
def add(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (y, (x, rest)) = stack
    if x.tag != "int" or y.tag != "int":
        fail(f"{x} cannot be multiplied by {y}")
    return (Int(x.value * y.value), rest), scope


def _simplify_fraction(numerator: int, denominator: int):
    gcd = math.gcd(numerator, denominator)
    return (numerator // gcd, denominator // gcd)


@module.register("%make")
def make_fraction(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (y, (x, rest)) = stack
    if x.tag != "int" or y.tag != "int":
        fail(f"{x} cannot be multiplied by {y}")

    if y.value == 0:
        fail(f"Construction of a zero-demoninator fraction: {x.value} 0 %make")

    numerator, denominator = _simplify_fraction(x.value, y.value)

    return (Vec([Int(numerator), Int(denominator)]), rest), scope


def _read_fraction(stack: T[V, Z], fail: Fail) -> tuple[tuple[int, int], Z]:
    (head, rest) = stack

    if head.tag == "int":
        return (head.value, 1), rest

    if head.tag != "vec":
        fail(f"{head} is not a fraction")

    if len(head.values) != 2:
        fail(f"{head} is not a fraction")

    xn, xm = head.values
    if xn.tag != "int" or xm.tag != "int":
        fail(f"{head} is not a fraction")

    return (xn.value, xm.value), rest


@module.register("%+")
def add_fractions(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (ya, yb), stack_ = _read_fraction(stack, fail)
    (xa, xb), stack__ = _read_fraction(stack_, fail)

    numerator, denominator = _simplify_fraction(xa*yb + xb*ya, xb*yb)

    return (Vec([Int(numerator), Int(denominator)]), stack__), scope


@module.register("%-")
def sub_fractions(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (ya, yb), stack_ = _read_fraction(stack, fail)
    (xa, xb), stack__ = _read_fraction(stack_, fail)

    numerator, denominator = _simplify_fraction(xa*yb - xb*ya, xb*yb)

    return (Vec([Int(numerator), Int(denominator)]), stack__), scope


@module.register("%*")
def mul_fractions(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (ya, yb), stack_ = _read_fraction(stack, fail)
    (xa, xb), stack__ = _read_fraction(stack_, fail)

    numerator, denominator = _simplify_fraction(xa*ya, xb*yb)

    return (Vec([Int(numerator), Int(denominator)]), stack__), scope


@module.register("%/")
def div_fractions(stack: T[V, T[V, S]], scope: Scope, fail: Fail):
    (ya, yb), stack_ = _read_fraction(stack, fail)
    (xa, xb), stack__ = _read_fraction(stack_, fail)

    if ya == 0:
        fail(f"Division by zero: ({xa} {xb}) ({ya} {yb}) %/")

    numerator, denominator = _simplify_fraction(xa*yb, xb*ya)

    return (Vec([Int(numerator), Int(denominator)]), stack__), scope