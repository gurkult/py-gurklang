from immutables import Map
from gurklang.vm import join_scopes


def scope(parent, id, **kwargs):
    return Map({
        "(parent)": parent,
        "(id)": id,
        **kwargs
    })


def test_join_scopes_None_and_closure_returns_closure():
    assert join_scopes(None, scope(parent=None, id=42)) == scope(None,42)

def test_join_scopes_None_and_main_returns_main():
    assert join_scopes(scope(parent=None, id=42), None) == scope(None,42)


def test_join_scopes_with_same_id_picks_main_scope():
    assert join_scopes(
        scope(parent=None, id=1, a=1, b=1),
        scope(parent=None, id=1, a=2, b=2),
    ) == scope(parent=None, id=1, a=1, b=1)


def test_join_scopes_deeply_updates_closure_scope_using_main_scope():
    assert join_scopes(
        scope(
            id=2,
            c=1000, d=100,
            parent=None
        ),
        scope(
            id=7,
            a=1, b=8,
            parent=scope(
                id=2,
                c=3, d=4,
                parent=None
            )
        ),
    ) == scope(
        id=7,
        a=1, b=8,
        parent=scope(
            id=2,
            c=1000, d=100,
            parent=None
        )
    )