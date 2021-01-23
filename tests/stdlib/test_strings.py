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


# it may be worth making a hypothesis test here, but IDK how to go about that
def test_delegated_methods():
    assert run("""
        :strings ( ->lower ->upper numeric? ) import
        "Hello WoRlD" ->lower
        "Hello WoRlD" ->upper
        "Hello WoRlD" numeric?
    """) == run("""'hello world' 'HELLO WORLD' :false""")


def test_join_list():
    assert run("""
        :strings (join-list) import
        ("A" ("B" ("CDEF" ()))) "," join-list
    """) == run("'A,B,CDEF'")
