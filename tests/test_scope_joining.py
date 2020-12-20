from gurklang.types import Scope
from immutables import Map


def test_joining_None_and_closure_returns_closure():
    assert (
        Scope(parent=None, id=42, values=Map()).join_closure_scope(None)
        == Scope(parent=None, id=42, values=Map())
    )


def test_joining_scopes_with_same_id_picks_main_scope():
    assert (
        Scope(None, 1, Map(a=1, b=1)).join_closure_scope(Scope(None, 1, Map(a=2, b=2)))
        == Scope(None, 1, Map(a=1, b=1))
    )


def test_joining_deeply_updates_closure_scope_using_main_scope():
    closure_scope = Scope(
        parent=Scope(None, 2, Map(c=3, d=4)),
        id=7,
        values=Map(a=1, b=8)
    )
    main_scope = Scope(
        parent=None,
        id=2,
        values=Map(c=1000, d=100)
    )

    assert (
        main_scope.join_closure_scope(closure_scope)
        == Scope(
            parent=Scope(None, 2, Map(c=1000, d=100)),
            id=7,
            values=Map(a=1, b=8)
        ))
