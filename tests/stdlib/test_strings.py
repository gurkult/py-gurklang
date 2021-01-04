from ..test_examples import run

def test_foreach_str():
    actual = run("""
    :math ( + ) import
    :boxes ( box <= -> ) import
    :strings ( ∀s ) import

    # count the number of `a`s in the string
    0 box :count def

    "nfhagiaaarnghroaafgfdanp" {
        dup println
        "a" = { 1 + } { } if
        count swap <=
    } ∀s

    count ->
    """)
    expected = run("7")

    assert expected == actual
