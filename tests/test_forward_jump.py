import pytest
import dis
from types import CodeType
from textwrap import dedent
from Resumption import (
    find_jump_pairs,
    patch_bytecode,
    JumpPair,
    Origin,
    Destination,
    DataLoad,
    DataType,
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
            ],
            data_loads = [
                DataLoad(
                    name = 5,
                    scope = 'simple_forward',
                    data_type = DataType.LOCAL,
                    instructions = [
                        dis.Instruction(opname='LOAD_CONST', opcode=100, arg=1, argval=5, argrepr='5', offset=2, starts_line=3, is_jump_target=False, positions=dis.Positions(lineno=3, end_lineno=3, col_offset=8, end_col_offset=9)),
                        dis.Instruction(opname='STORE_FAST', opcode=125, arg=0, argval='a', argrepr='a', offset=4, starts_line=None, is_jump_target=False, positions=dis.Positions(lineno=3, end_lineno=3, col_offset=4, end_col_offset=5)),
                    ],
                ),
                DataLoad(
                    name = 7,
                    scope = 'simple_forward',
                    data_type = DataType.LOCAL,
                    instructions = [
                        dis.Instruction(opname='LOAD_CONST', opcode=100, arg=2, argval=7, argrepr='7', offset=38, starts_line=5, is_jump_target=False, positions=dis.Positions(lineno=5, end_lineno=5, col_offset=8, end_col_offset=9)),
                        dis.Instruction(opname='STORE_FAST', opcode=125, arg=0, argval='a', argrepr='a', offset=40, starts_line=None, is_jump_target=False, positions=dis.Positions(lineno=5, end_lineno=5, col_offset=4, end_col_offset=5)),
                    ],
                ),
            ]
        )
    ]



@pytest.mark.parametrize("source", [7], indirect = True)
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
    dis.dis(patched_code)
    exec(patched_code, {})
