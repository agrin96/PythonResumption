import pytest
from types import CodeType
from textwrap import dedent
from Resumption import (
    find_jump_pairs,
    MissingDestinationError,
)


@pytest.fixture(scope = "module")
def source_name() -> str:
    return "test_missing_destination.py"



@pytest.fixture(scope = "module")
def source(source_name: str) -> CodeType:
    raw_source = dedent("""
    def dangling_label():
        a = 5
        GOTO .test
        a = 7
        assert a == 5, F"Jump not executed successfully since {{a=}} and not 5"

    dangling_label()
    """)
    return compile(
        source = raw_source,
        filename = source_name,
        mode = "exec",
    )



def test_missing_destination(source: CodeType) -> None:
    with pytest.raises(MissingDestinationError):
        _ = find_jump_pairs(code = source)