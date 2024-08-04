import pytest
from types import CodeType
from textwrap import dedent
from Resumption import (
    find_jump_pairs,
    DuplicateDestinationsError,
)


@pytest.fixture(scope = "module")
def source_name() -> str:
    return "test_duplicate_destinations.py"



@pytest.fixture(scope = "module")
def source(source_name: str) -> CodeType:
    raw_source = dedent("""
    def dangling_label():
        a = 5
        GOTO .test
        a = 7
        LABEL .test
        assert a == 5, F"Jump not executed successfully since {{a=}} and not 5"
        LABEL .test

    dangling_label()
    """)
    return compile(
        source = raw_source,
        filename = source_name,
        mode = "exec",
    )



def test_duplicate_destinations(source: CodeType) -> None:
    with pytest.raises(DuplicateDestinationsError):
        _ = find_jump_pairs(code = source)