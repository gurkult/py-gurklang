from typing import Union
from gurklang.types import Int, Str
from .native_utils import forall, comparables


@forall(Int, Int)
def test_swap_is_own_inverse(postulate):
    """
    :b var :a var

    a b swap swap

    b = swap a = &&
    """

@forall(Int, Int, Int)
def test__rot_rot_rot__is_id(postulate):
    """
    :c var :b var :a var

    a b c rot rot rot

    c = swap b = && swap a = &&
    """