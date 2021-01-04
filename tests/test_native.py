from typing import Union
from gurklang.types import Int, Str
from .native_utils import forall, comparables


@forall(Int, Int)
def test_swap_is_own_inverse():
    """
    :b def :a def

    a b swap swap

    b = swap a = &&
    """

@forall(Int, Int, Int)
def test__rot_rot_rot__is_id():
    """
    :c def :b def :a def

    a b c rot rot rot

    c = swap b = && swap a = &&
    """