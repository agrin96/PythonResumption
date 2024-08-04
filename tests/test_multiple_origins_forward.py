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
    return "test_multiple_origin_jumps_forward.py"



@pytest.fixture(scope = "module")
def source(request: pytest.FixtureRequest, source_name: str) -> CodeType:
    raw_source = dedent(F"""
    def simple_forward(arg):
        a = 3
        if arg == 0:
            GOTO .test
        a = 5
        GOTO .test
        a = 7
        LABEL .test
        assert a == {request.param[1]}, F"Jump not executed successfully since {{a=}} and not {request.param[1]}"
    
    simple_forward({request.param[0]})
    """)
    print(raw_source)
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
                    scope_name = 'simple_forward',
                    filename = source_name,
                    line = 5,
                    byte_offsets = [16, 26, 46],
                    is_complete = True
                ),
                Origin(
                    scope_name = 'simple_forward',
                    filename = source_name,
                    line = 7,
                    byte_offsets = [52, 82],
                    is_complete = True,
                ),
            ],
            destination = [
                Destination(
                    scope_name = 'simple_forward',
                    filename = source_name,
                    line = 9,
                    byte_offsets = [88, 98, 118],
                    is_complete = True
                )
            ]
        )
    ]



@pytest.mark.parametrize(
    "source",
    [(0, 3), (1, 5)],
    indirect = True,
)
def test_multiple_origin_jumps_forward(
        source: CodeType,
        jumps: list[JumpPair]
    ) -> None:
    jump_pairs = find_jump_pairs(code = source)
    assert jump_pairs == jumps, "Jump pairs not generated correctly"
    
    patched_code = patch_bytecode(
        code = source,
        jump_pairs = jump_pairs,
    )
    exec(patched_code, {}, {})