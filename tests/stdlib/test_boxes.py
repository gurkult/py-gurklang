from gurklang.types import Int
from ..native_utils import forall
from ..test_examples import run


@forall(Int)
def test_box_stores_given_value():
    """
    :boxes ( box -> ) import

    :x def

    x box :b def

    {b ->}, {x}, =
    """


@forall(Int, Int)
def test_two_boxes_can_coexist():
    """
    :boxes ( box -> ) import
    :x def :y def

    x box :x-box def
    y box :y-box def

    {x-box ->}, {x}, =
    {y-box ->}, {y}, =
    {x-box ->}, {x}, =
    {y-box ->}, {y}, =
    """


@forall(Int, Int, Int)
def test_three_boxes_can_coexist():
    """
    :boxes ( box -> ) import
    :x def :y def :z def

    x box :x-box def
    y box :y-box def
    z box :z-box def

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
    :x def :y def
    :a def :b def

    x box :x-box def
    y box :y-box def
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

    :x def

    x box :b def

    {b ->}, {x}, =
    {b ->}, {x}, =
    {b ->}, {x}, =
    """


@forall(Int, Int)
def test_box_can_change_its_value():
    """
    :boxes ( box -> <= ) import

    :x def  :y def

    x box :b def

    b { drop y } <=
    {b ->}, {y}, =
    """


@forall(Int, Int, Int)
def test_box_can_change_its_value_twice():
    """
    :boxes ( box -> <= ) import
    :x def  :y def  :z def

    x box :b def

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
    :x def :y def

    x box :b def

    b <[
    b y <-

    { {1 {y {x ()},}, }, }, boxes? =
    """


@forall(Int, Int)
def test_simple_read_reads_the_bottom_value_of_box():
    """
    :boxes ( box -> <- <[ ) import
    :x def :y def

    x box :b def

    b <[
    b y <-

    {b ->}, {x}, =
    """


@forall(Int, Int, Int)
def test_top_read_reads_the_value_of_box_from_latest_transaction():
    """
    :boxes ( box -!> <- <[ ) import
    :x def :y def :z def

    x box :b def

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
    :x def :y def

    x box :b def

    b { drop y } <=

    {b ->}, {y}, =
    """


@forall(Int, Int)
def test_change_passes_current_value_to_function():
    """
    :math  ( +         ) import
    :boxes ( box -> <= ) import
    :x def :y def

    x box :b def

    b { y + } <=

    {b ->}, {x y +}, =
    """


@forall(Int, Int)
def test_equivalent_implementaiton_of_change():
    """
    :math  ( +                   ) import
    :boxes ( box -!> -> <- <= <[ ]> ) import
    :x def :y def

    {
      :fn def :a-box def
        a-box <[
            a-box -!> fn !
            a-box swap <-
        a-box ]>
    } :my-<= jar

    x box :a def
    x box :b def

    a { y + } my-<=
    b { y + } <=

    {a ->}, {b ->}, =
    """


@forall(Int, Int)
def test_when_transaction_is_in_progess_old_value_is_seen():
    """
    :boxes   ( box -!> -> <- <= <[ ]> ) import
    :x def :y def

    x box :b def
    :nil box :b-inside def

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
    :x def :y def

    x box :b def

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
    :x def :y def

    x box :b def

    b <[

    b y <-

    {b <<<?}, {y}, =
    {b ->},   {x}, =
    {b -!>},  {x}, =
    && &&
    """