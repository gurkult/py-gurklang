"""
Visualizing execution with manim

Make sure you install `manimce`, see instructions at
https://docs.manim.community/en/v0.1.1/installation.html

Note: manim seems to be slower on PyPy, so run this in CPython.

Scroll to the bottom to see a usage example
"""

import re
from itertools import zip_longest
from functools import reduce
from typing import Iterator, List,  Tuple, Type

try:
    import manim
    from manim import *  # type: ignore
except ImportError:
    manim = None

from gurklang.vm import run_with_middleware
from gurklang.types import Value, Stack, Instruction, Code
from gurklang.parser import parse


def _escape_latex(text: str) -> str:
    replacements = (
        ('\\', R'\textbackslash '),
        ('&', R'\&'),
        ('%', R'\%'),
        ('$', R'\$'),
        ('#', R'\#'),
        ('_', R'\_'),
        ('{', R'\{'),
        ('}', R'\}'),
        ('~', R'\textasciitilde{}'),
        ('^', R'\^{}'),
        ('<', R'\textless{}'),
        ('>', R'\textgreater{}'),
    )

    def single_replacement(source: str, replacement: Tuple[str, str]):
        old, new = replacement
        return source.replace(old, new)

    return reduce(single_replacement, replacements, text)


def _escape_function_name(name: str) -> str:
    # LaTeX doesn't like the λ character
    if name == "λ":
        return R"$\lambda$"
    else:
        return _escape_latex(name)


def _format_source_as_latex(source: str) -> str:
    source = re.sub(r"\#.*(?=$|\n)", "", source)
    source = re.sub(r"\s+", " ", source)
    return R"\texttt{" + _escape_latex(source) + "}"


def _render_code(value: Code) -> str:
    if value.name != "λ" or value.source_code is None:
        return _escape_function_name(value.name)
    return _format_source_as_latex(value.source_code)


def _render_value(value: Value) -> str:
    lookup = {
        "atom":   lambda v: R"\texttt{:" + _escape_latex(v.value) + R"}",
        "str":    lambda v: _escape_latex(repr(v.value)),
        "int":    lambda v: _escape_latex(str(v.value)),
        "vec":    lambda v: R"$\left(\text{" + " ".join(map(_render_value, v.values)) + R"}\right)$",
        "native": lambda v: _escape_function_name(v.name),
        "code":   _render_code
    }
    return lookup[value.tag](value)


def _stacks_in_reverse(stack: Stack) -> Iterator[Stack]:
    """
    >>> [*_stacks_in_reverse( (1, (2, None)) )]
    [None, (2, None), (1, (2, None))]
    """
    if stack is None:
        yield None
    else:
        (_, rest) = stack
        yield from _stacks_in_reverse(rest)
        yield stack


def _stack_divergence(old_stack: Stack, new_stack: Stack):
    """
    >>> root = (2, 1, None)
    >>> [*_stack_divergence( (3, root), ("b", ("a", root)) )]
    [
        ('same',      None,                None                         ),
        ('same',      (1, None),           (1, None)                    ),
        ('same',      (2, (1, None)),      (2, (1, None))               ),
        ('different', (3, (2, (1, None))), ("a", (2, (1, None)))        ),
        ('different', TOO_LONG,            ("b", ("a", (2, (1, None)))) ),
    ]
    """
    for (x, y) in zip_longest(
        _stacks_in_reverse(old_stack),
        _stacks_in_reverse(new_stack),
        fillvalue=_stack_divergence.TOO_LONG
    ):
        if x is y:
            yield ("same", x, y)
        else:
            yield ("different", x, y)
_stack_divergence.TOO_LONG = object()


def _stack_diff(old_stack: Stack, new_stack: Stack) -> Tuple[int, List[Value]]:
    """
    Compute how to chage the old_stack to get to the new_stack.

    Returns a tuple containing:
    0. The number of elements to be deleted
    1. A list of elements to be added afterwards
    """

    total_diff_length = 0
    total_extra_elements = 0
    added: List[Value] = []

    for tag, x, y in _stack_divergence(old_stack, new_stack):
        if tag == "same":
            continue
        total_diff_length += 1
        if x is _stack_divergence.TOO_LONG:
            total_extra_elements += 1
        if y is not _stack_divergence.TOO_LONG:
            added.append(y[0])

    deleted = total_diff_length - total_extra_elements
    return (deleted, added)


class StackDisplay:
    cells: List["Mobject"]

    def __init__(self, scene: "Scene"):
        self.scene = scene
        self.stack = None
        self.cells = [Point(ORIGIN)]
        self.group = Group()

    def update(self, new_stack: Stack):
        deleted, added = _stack_diff(self.stack, new_stack)
        self._remove_top_n_cells(deleted)
        for value in added:
            self._push_new_value(value)
        self.scene.wait(0.5)
        self.stack = new_stack

    def _remove_top_n_cells(self, n: int):
        for _ in range(n):
            cell = self.cells.pop()
            self.scene.play(FadeOutAndShift(cell, direction=RIGHT, run_time=0.2))
            self.group.remove(cell)

    def _add_new_cell(self, cell: "Mobject"):
        cell.move_to(self.cells[-1]).shift(UP * 0.72)
        self.cells.append(cell)
        self.group.add(cell)
        self.scene.play(FadeInFrom(cell, direction=LEFT, run_time=0.2))
        self._arrange()
        self.scene.wait(0.15)
        self.scene.play(FadeToColor(cell, color="#ffffff", run_time=0.3))

    def _push_new_value(self, value: Value):
        rect = Rectangle(width=12.0, height=0.68)
        label = Tex(_render_value(value)).scale(0.8).move_to(rect)
        cell = Group(rect, label).set_color("#78ff90")
        self._add_new_cell(cell)
        if value.tag == "code":
            self._reveal_source_code(value, label, cell)

    def _reveal_source_code(self, code: Code, label: "Tex", cell: "Group"):
        if code.name == "λ" or code.source_code is None:
            return
        new_label = Tex(_format_source_as_latex(code.source_code)).scale(0.8).move_to(label)
        self.scene.play(Transform(label, new_label, run_time=1.0))
        cell.remove(label)
        cell.add(new_label)
        self.scene.wait(0.5)

    def _arrange(self):
        # this will "smoothly call" self.group.arrange(direction=UP) over 0.15 seconds
        animations = self.scene.compile_play_args_to_animation_list(
            self.group.arrange, {"direction": UP},
            run_time=0.2,
        )
        self.scene.play(*animations)


def visualize(name: str, source_code: str) -> Type["Scene"]:
    if manim is None:
        raise RuntimeError("manim is not installed. Check out https://docs.manim.community/en/v0.1.1/installation.html")

    class Visualization(Scene):
        def construct(self) -> None:
            self.wait(0.1)
            display = StackDisplay(self)
            self.wait(0.1)

            def middleware(i: Instruction, old: Stack, new: Stack):
                if new is not old:
                    display.update(new)

            run_with_middleware(parse(source_code), middleware)

            self.wait(3)

    Visualization.__name__ = name
    return Visualization


# Manim assigns `py` as __name__. Don't know why.
if __name__ == "py":
    # python -m manim path/to/file.py FactorialRecursive -ql
    FactorialRecursive = visualize(
        "FactorialRecursive",
        R"""
            :math ( + - < * ) import

            {
                dup 2 <
                { drop 1 }
                { dup 1 - n! * }
                if !
            } :n! jar

            3 n! println
        """
    )

    # python -m manim path/to/file.py FactorialTCO -ql
    FactorialTCO = visualize(
        "FactorialTCO",
        R"""
            :math ( + - < * ) import

            { }
            :id jar

            { dup 1 - rot3 * swap n!-impl }
            :n!-step jar

            { dup 2 < {id} {n!-step} if ! } parent-scope
            :n!-impl jar

            { 1 swap n!-impl drop }
            :n! jar

            4 n! println
        """)