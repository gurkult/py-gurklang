from gurklang.types import Int
from ..native_utils import forall
from ..test_examples import run


@forall(Int)
def test_box_stores_given_value():
    """
    :boxes ( box -> ) import

    :x var

    x box :b var

    {b ->}, {x}, =
    """


@forall(Int, Int)
def test_box_can_change_its_value():
    """
    :boxes ( box -> <= ) import

    :x var  :y var

    x box :b var

    b { drop y } <=
    {b ->}, {y}, =
    """


@forall(Int, Int, Int)
def test_box_can_change_its_value_twice():
    """
    :boxes ( box -> <= ) import
    :x var  :y var  :z var

    x box :b var

    b { drop y } <=
    {b ->}, {y}, =

    b { drop z } <=
    {b ->}, {z}, =

    &&
    """
