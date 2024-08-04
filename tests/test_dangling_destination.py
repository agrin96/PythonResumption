import pytest
from types import CodeType
from textwrap import dedent
from Resumption import (
    find_jump_pairs,
    MissingOriginError,
)


@pytest.fixture(scope = "module")
def source_name() -> str:
    return "test_dangling_destination.py"



@pytest.fixture(scope = "module")
def source(source_name: str) -> CodeType:
    raw_source = dedent("""
    def dangling_label():
        a = 5
        a = 7
        LABEL .test
        assert a == 5, F"Jump not executed successfully since {{a=}} and not 5"

    dangling_label()
    """)
    return compile(
        source = raw_source,
        filename = source_name,
        mode = "exec",
    )



def test_dangling_destination(source: CodeType) -> None:
    with pytest.raises(MissingOriginError):
        _ = find_jump_pairs(code = source)