import pytest
from types import CodeType
from textwrap import dedent
from Resumption import (
    find_jump_pairs,
    patch_bytecode,
    JumpPair,
    Origin,
    Destination,
)


@pytest.fixture(scope = "module")
def source_name() -> str:
    return "test_simple_jump_forward.py"



@pytest.fixture(scope = "module")
def source(request: pytest.FixtureRequest, source_name: str) -> CodeType:
    raw_source = dedent(F"""
    def simple_forward():
        a = 5
        GOTO .test
        a = 7
        LABEL .test
        assert a == {request.param}, F"Jump not executed successfully since {{a=}} and not {request.param}"

    simple_forward()
    """)
    return compile(
        source = raw_source,
        filename = source_name,
        mode = "exec",
    )



@pytest.fixture(scope = "module")
def jumps(source_name: str) -> list[JumpPair]:
    return [
        JumpPair(
            name = "test",
            origin = [
                Origin(
                    scope_name = "simple_forward",
                    filename = source_name,
                    line = 4,
                    byte_offsets = [6, 16, 36],
                    is_complete = True,
                ),
            ],
            destination = [
                Destination(
                    scope_name = 'simple_forward',
                    filename = source_name,
                    line = 6,
                    byte_offsets = [42, 52, 72],
                    is_complete = True
                )
            ]
        )
    ]



@pytest.mark.parametrize("source", [5], indirect = True)
def test_simple_jump_forward(
        source: CodeType,
        jumps: list[JumpPair],
    ) -> None:
    jump_pairs = find_jump_pairs(code = source)
    assert jump_pairs == jumps, "Jump pairs not generated correctly"
    
    patched_code = patch_bytecode(
        code = source,
        jump_pairs = jump_pairs,
    )
    exec(patched_code, {}, {})
