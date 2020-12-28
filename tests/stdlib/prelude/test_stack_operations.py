from gurklang.types import Int
from ...native_utils import forall


@forall(Int)
def test_dup():
    """
    :a def

    {a dup}, {a a}, =
    """


@forall(Int, Int)
def test_2dup():
    """
    :b def :a def

    {a b 2dup}, {a b a b}, =
    """


@forall(Int, Int)
def test_drop():
    """
    :b def :a def

    {a b drop}, {a}, =
    """


@forall(Int, Int, Int)
def test_2drop():
    """
    :c def :b def :a def

    {a b c 2drop}, {a}, =
    """


@forall(Int, Int)
def test_swap():
    """
    :b def :a def

    {a b swap}, {b a}, =
    """


@forall(Int, Int)
def test_over():
    """
    :b def :a def

    {a b over}, {a b a}, =
    """


@forall(Int, Int, Int)
def test_unrot():
    """
    :c def :b def :a def

    {a b c unrot}, {c a b}, =
    """


@forall(Int, Int, Int)
def test_rot():
    """
    :c def :b def :a def

    {a b c rot}, {b c a}, =
    """


@forall(Int, Int, Int)
def test__rot_rot__is_unrot():
    """
    :c def :b def :a def

    {a b c rot rot}, {a b c unrot}, =
    """

@forall(Int, Int, Int)
def test__rot_rot_rot__is_id():
    """
    :c def :b def :a def

    {a b c rot rot rot}, {a b c}, =
    """
