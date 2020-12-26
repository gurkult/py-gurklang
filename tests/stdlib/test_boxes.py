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
def test_two_boxes_can_coexist():
    """
    :boxes ( box -> ) import
    :x var :y var

    x box :x-box var
    y box :y-box var

    {x-box ->}, {x}, =
    {y-box ->}, {y}, =
    {x-box ->}, {x}, =
    {y-box ->}, {y}, =
    """


@forall(Int, Int, Int)
def test_three_boxes_can_coexist():
    """
    :boxes ( box -> ) import
    :x var :y var :z var

    x box :x-box var
    y box :y-box var
    z box :z-box var

    {x-box ->}, {x}, =
    {y-box ->}, {y}, =
    {z-box ->}, {z}, =
    {x-box ->}, {x}, =
    {y-box ->}, {y}, =
    {z-box ->}, {z}, =
    """


@forall(Int, Int, Int, Int)
def test_two_boxes_are_mutated_correctly():
    """
    :boxes ( box -> <- ) import
    :x var :y var
    :a var :b var

    x box :x-box var
    y box :y-box var
    x-box a <-
    y-box b <-

    {x-box ->}, {a}, =
    {y-box ->}, {b}, =
    {x-box ->}, {a}, =
    {y-box ->}, {b}, =
    """


@forall(Int)
def test_box_holds_on_to_its_value():
    """
    :boxes ( box -> ) import

    :x var

    x box :b var

    {b ->}, {x}, =
    {b ->}, {x}, =
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


@forall(Int, Int)
def test_write_replaces_topmost_value_of_box():
    """
    :inspect ( boxes? ) import
    :boxes ( box <- <[ ) import
    :x var :y var

    x box :b var

    b <[
    b y <-

    { {1 {y {x ()},}, }, }, boxes? =
    """


@forall(Int, Int)
def test_simple_read_reads_the_bottom_value_of_box():
    """
    :boxes ( box -> <- <[ ) import
    :x var :y var

    x box :b var

    b <[
    b y <-

    {b ->}, {x}, =
    """


@forall(Int, Int, Int)
def test_top_read_reads_the_value_of_box_from_latest_transaction():
    """
    :boxes ( box -!> <- <[ ) import
    :x var :y var :z var

    x box :b var

    b <[  b y <-

    {b -!>}, {y}, =

    b <[  b z <-

    {b -!>}, {z}, =

    &&
    """


@forall(Int, Int)
def test_change():
    """
    :boxes ( box -> <= ) import
    :x var :y var

    x box :b var

    b { drop y } <=

    {b ->}, {y}, =
    """


@forall(Int, Int)
def test_change_passes_current_value_to_function():
    """
    :math  ( +         ) import
    :boxes ( box -> <= ) import
    :x var :y var

    x box :b var

    b { y + } <=

    {b ->}, {x y +}, =
    """


@forall(Int, Int)
def test_equivalent_implementaiton_of_change():
    """
    :math  ( +                   ) import
    :boxes ( box -!> -> <- <= <[ ]> ) import
    :x var :y var

    {
      :fn var :a-box var
        a-box <[
            a-box -!> fn !
            a-box swap <-
        a-box ]>
    } :my-<= jar

    x box :a var
    x box :b var

    a { y + } my-<=
    b { y + } <=

    {a ->}, {b ->}, =
    """


@forall(Int, Int)
def test_when_transaction_is_in_progess_():
    """
    :boxes   ( box -!> -> <- <= <[ ]> ) import
    :x var :y var

    x box :b var
    :nil box :b-inside var

    b <[
        b y <-
        b-inside  b ->  <-
    b ]>

    {b-inside ->  b ->}, {x y}, =
    """


@forall(Int, Int)
def test_rollback_reverts_the_topmost_transaction():
    """
    :boxes ( box -> -!> <- <<< <[ ]> ) import
    :x var :y var

    x box :b var

    b <[

    b y <-

    {b <<<}, ()   =
    {b ->},  {x}, =
    {b -!>}, {x}, =
    && &&
    """


@forall(Int, Int)
def test_rollback_with_question_mark_also_pops_the_intermediate_result():
    """
    :boxes ( box -> -!> <- <<<? <[ ]> ) import
    :x var :y var

    x box :b var

    b <[

    b y <-

    {b <<<?}, {y}, =
    {b ->},   {x}, =
    {b -!>},  {x}, =
    && &&
    """