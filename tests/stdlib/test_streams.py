from ..test_examples import run


def test_string_stream():
    assert run("""
    :streams (str->stream) import
    '123' str->stream 
    ! swap
    ! swap
    ! swap
    ! nip
    """) == run("'1' '2' '3' :stream-end")
