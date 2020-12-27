from gurklang.types import Int
from ...native_utils import forall


@forall(Int)
def test_dup():
    """
    :a var

    {a dup}, {a a}, =
    """


@forall(Int, Int)
def test_2dup():
    """
    :b var :a var

    {a b 2dup}, {a b a b}, =
    """


@forall(Int, Int)
def test_drop():
    """
    :b var :a var

    {a b drop}, {a}, =
    """


@forall(Int, Int, Int)
def test_2drop():
    """
    :c var :b var :a var

    {a b c 2drop}, {a}, =
    """


@forall(Int, Int)
def test_swap():
    """
    :b var :a var

    {a b swap}, {b a}, =
    """


@forall(Int, Int)
def test_over():
    """
    :b var :a var

    {a b over}, {a b a}, =
    """


@forall(Int, Int, Int)
def test_unrot():
    """
    :c var :b var :a var

    {a b c unrot}, {c a b}, =
    """


@forall(Int, Int, Int)
def test_rot():
    """
    :c var :b var :a var

    {a b c rot}, {b c a}, =
    """


@forall(Int, Int, Int)
def test__rot_rot__is_unrot():
    """
    :c var :b var :a var

    {a b c rot rot}, {a b c unrot}, =
    """

@forall(Int, Int, Int)
def test__rot_rot_rot__is_id():
    """
    :c var :b var :a var

    {a b c rot rot rot}, {a b c}, =
    """
