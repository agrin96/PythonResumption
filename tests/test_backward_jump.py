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
    DataType,
    DataLoad,
)


@pytest.fixture(scope = "module")
def source_name() -> str:
    return "test_simple_jump_backward.py"



@pytest.fixture(scope = "module")
def source(request: pytest.FixtureRequest, source_name: str) -> CodeType:
    raw_source = dedent("""
    def simple_backward():
        a = 5
        if a == 3:
            LABEL .test
            a = 7
            assert a == 7, F"Jump not executed successfully since {a=} and not 7"
            return
        GOTO .test

    simple_backward()
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
            name = 'test',
            origin = [
                Origin(
                    scope_name = 'simple_backward',
                    filename = source_name,
                    line = 9,
                    byte_offsets = [86, 96, 116],
                    is_complete = True,
                )
            ],
            destination = [
                Destination(
                    scope_name = 'simple_backward',
                    filename = source_name,
                    line = 5,
                    byte_offsets = [16, 26, 46],
                    is_complete = True,
                )
            ],
            data_loads = [
                 DataLoad(
                     name = 5,
                     scope = 'simple_backward',
                     data_type = DataType.LOCAL,
                     instructions = [
                        dis.Instruction(opname='LOAD_CONST', opcode=100, arg=1, argval=5, argrepr='5', offset=2, starts_line=3, is_jump_target=False, positions=dis.Positions(lineno=3, end_lineno=3, col_offset=8, end_col_offset=9)),
                        dis.Instruction(opname='STORE_FAST', opcode=125, arg=0, argval='a', argrepr='a', offset=4, starts_line=None, is_jump_target=False, positions=dis.Positions(lineno=3, end_lineno=3, col_offset=4, end_col_offset=5)),
                    ],
                 ),
                 DataLoad(
                     name = 7,
                     scope = 'simple_backward',
                     data_type = DataType.LOCAL,
                     instructions = [
                        dis.Instruction(opname='LOAD_CONST', opcode=100, arg=3, argval=7, argrepr='7', offset=48, starts_line=6, is_jump_target=False, positions=dis.Positions(lineno=6, end_lineno=6, col_offset=12, end_col_offset=13)),
                        dis.Instruction(opname='STORE_FAST', opcode=125, arg=0, argval='a', argrepr='a', offset=50, starts_line=None, is_jump_target=False, positions=dis.Positions(lineno=6, end_lineno=6, col_offset=8, end_col_offset=9)),
                    ],
                 ),
            ]
        )
    ]



@pytest.mark.parametrize("source", [5], indirect = True)
def test_jump_backward(
        source: CodeType,
        jumps: list[JumpPair],
    ) -> None:
    jump_pairs = find_jump_pairs(code = source)
    assert jump_pairs == jumps, "Jump pairs not generated correctly"
    
    patched_code = patch_bytecode(
        code = source,
        jump_pairs = jump_pairs,
    )
    exec(patched_code, {})
