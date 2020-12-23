from typing import List
from gurklang.types import Atom, Instruction, Int, Stack, Value
import pprint
import gurklang.vm as vm
from gurklang.vm_utils import repr_stack
from gurklang.parser import parse


source1 = R"""
{ :b var :a var b a } :my_swap jar
1 2 3 4 my_swap
"""

source2 = R"""
:math ( + ) import

{ :x var { x + } } :make_adder jar
5 make_adder :add5 jar

"Answer:" print
37 add5 print
37 { add5 } ! print
"""

source3 = R"""
{1} {2} :true if print

{1} {2} :false if print
"""

source4 = r"""
:math :qual import

160 15 :%make math   # 160 15 %make      ~  (32 3)
4 10 :%make math     # 4 10 %make        ~  (2 5)
:%+ math print       # (23 3) (4 10) %+  ~  (166 15)
"""


source5 = r"""
# 1. Only import certain names (from math import %make)
:math (%make) import
4 2 %make print

# 2. Import all the names (from math import *)
:math :all import
4 2 %make print

# 3. Qualified import (import math)
:math :qual import
4 2 :%make math print

# 4. Renaming qualified import (import math as shmath)
:math :as:shmath import
4 2 :%make shmath print

# 5. Prefixed import (from math import * as "math_*")
:math :prefix import
4 2 math.%make print

# 6. Custom prefixed import (from math import * as "math_*")
:math :prefix:shmath import
4 2 shmath.%make print
"""


source6 = R"""
:math ( + ) import
:inspect ( code-dump ) import

{ :f var :x var { x f ! } } :my-close jar

{ { + } my-close } :make-adder jar

5 make-adder :add5 jar

37 add5 print  #=> 42
40 add5 print  #=> 45
"""


source7 = R"""
:math ( + - < * ) import

{ dup 2 <
  { drop 1 } parent-scope
  { dup 1 - n! * } parent-scope
  if !
} parent-scope :n! jar

10000 n! println
"""


source8 = R"""
:math ( + - < * ) import

{
  dup 2 <
    { }
    { dup 1 - rot3 * swap n!-impl } parent-scope
    if !
} parent-scope :n!-impl jar

{ 1 swap n!-impl drop } parent-scope :n! jar

100000 n! drop
"""


source9 = R"""
:inspect :prefix import
:math ( + - < * ) import

{
  dup 2 <
  { drop 1 } parent-scope
  { dup 1 - n! * } parent-scope
  if !
} parent-scope :n! jar

:n! inspect.dis
"""


from manim import *
import re

def tex_escape(text: str) -> str:
    return (
        text
        .replace('\\', R'\textbackslash ')
        .replace('&', R'\&')
        .replace('%', R'\%')
        .replace('$', R'\$')
        .replace('#', R'\#')
        .replace('_', R'\_')
        .replace('{', R'\{')
        .replace('}', R'\}')
        .replace('~', R'\textasciitilde{}')
        .replace('^', R'\^{}')
        .replace('<', R'\textless{}')
        .replace('>', R'\textgreater{}')
    )


def draw_value(value: Value) -> str:
    if value.tag == "atom":
        return R"\texttt{:" + tex_escape(value.value) + R"}"
    elif value.tag == "str":
        return tex_escape(repr(value.value))
    elif value.tag == "int":
        return tex_escape(str(value.value))
    elif value.tag == "vec":
        return R"$\left(\text{" + " ".join(map(draw_value, value.values)) + R"}\right)$"
    elif value.tag == "native" or value.source_code is None:
        return tex_escape(value.name) if value.name != "λ" else R"$\lambda$"
    else:
        # remove comments and indents from source:
        source = re.sub(r"\#.*(?=$|\n)", "", value.source_code)
        source = re.sub(r"\s+", " ", source)
        return R"\texttt{" + tex_escape(source) + "}"


def draw_stack(stack: Stack) -> str:
    if stack is None:
        return R"$\emptyset$"
    head, rest = stack
    return RF"({draw_value(head)}, {draw_stack(rest)})"

def build_up_stack(scene: Scene, stack):
    src = R"$\emptyset$"
    tex = Tex(src)
    yield FadeIn(tex)
    while stack is not None:
        head, stack = stack
        src = f"({head}, {src})"
        yield Transform(tex, Tex(src))


from itertools import zip_longest


def stacks_in_reverse(stack):
    if stack is None:
        yield None
    else:
        _, rest = stack
        yield from stacks_in_reverse(rest)
        yield stack


def updates(stack1, stack2):
    for (x, y) in zip_longest(stacks_in_reverse(stack1), stacks_in_reverse(stack2), fillvalue=updates.TOO_LONG):
        if x is y:
            yield ("same", x, y)
        else:
            yield ("different", x, y)
updates.TOO_LONG = object()


config.max_files_cached = 1000


def stack_diff(old_stack: Stack, new_stack: Stack):
    total = 0
    extra = 0
    added: List[Value] = []
    for tag, x, y in updates(old_stack, new_stack):
        if tag == "different":
            total += 1
            if x is updates.TOO_LONG:
                extra += 1
            if y is not updates.TOO_LONG:
                added.append(y[0])
    delete = total - extra
    return (delete, added)


class StackDisplay:
    elements: List[Mobject]

    def __init__(self, scene: Scene):
        self.scene = scene
        self.stack = None
        self.elements = []
        self.group = Group()

    def update(self, new_stack: Stack):
        delete, add = stack_diff(self.stack, new_stack)
        print("stack =", self.stack)
        print("new stack =", new_stack)
        print("diff =", delete, add)
        print()
        if delete > 0:
            for e in self.elements[-delete:][::-1]:
                print("removing", e)
                self.scene.play(FadeOutAndShift(e, direciton=RIGHT, run_time=0.1))
                self.group.remove(e)
                self.elements.pop()
        for value in add:
            rect = Rectangle(width=12.0, height=0.68)
            text = Tex(draw_value(value)).scale(0.8).move_to(rect)
            cell = Group(rect, text).set_color("#78ff90")
            if self.elements != []:
                cell.move_to(self.elements[-1]).shift(UP * 0.72)
            self.elements.append(cell)
            self.group.add(cell)
            self.scene.play(FadeInFrom(cell, direction=LEFT, run_time=0.1))
            self.scene.play(*self.arrange())
            self.scene.play(FadeToColor(cell, color="#ffffff", run_time=0.1))
        if delete > 0 or add != []:
            self.scene.wait(0.2)
        self.stack = new_stack

    def arrange(self) -> List[Animation]:
        return self.scene.compile_play_args_to_animation_list(
            self.group.arrange, dict(direction=UP, center=True),
            run_time=0.05,
        )



class Visualization(Scene):
    def construct(self):
        source = R"""
            :math ( + - < * ) import

            {
                dup 2 <
                { drop 1 }
                { dup 1 - n! * }
                if !
            } :n! jar

            5 n! println
        """

        self.wait(0.1)
        display = StackDisplay(self)
        self.wait(0.1)

        def middleware(i: Instruction, old: Stack, new: Stack):
            if new is not old:
                display.update(new)

        vm.run_with_middleware(parse(source), middleware)

        self.wait(3)





# stack, scope = vm.run(parse(source8))

# print("\n----------------")
# print("Resulting stack:")
# pprint.pprint(repr_stack(stack))