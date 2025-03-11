import sys
from pathlib import Path
from _pytest.fixtures import fixture

TESTS_DIR = Path(__file__).parent
TOOLS_DIR = TESTS_DIR.parent
CODE_GEN_DIR = TOOLS_DIR / "code_gen"
OUT_DIR = TESTS_DIR / "test_output"

sys.path.append(TOOLS_DIR.as_posix())
sys.path.append(CODE_GEN_DIR.as_posix())

# noinspection PyUnresolvedReferences
from api_def import ApiDef

# noinspection PyUnresolvedReferences
from swift_generator import SwiftBindingGenerator, SwiftGenerator

#
# fixtures
#


@fixture
def api_minimal_valid() -> dict:
    return dict(
        name="test_api",
        version="1.2.3",
        constants=[dict(type="int32", name="the_const", value="1")],
    )


@fixture
def api_with_list() -> dict:
    return dict(
        name="test_api",
        version="1.2.3",
        classes=[
            dict(
                name="TheClass",
                methods=[
                    dict(
                        type="float64",
                        name="list_sum",
                        parameters=[
                            dict(name="label", type="string", is_const=True),
                            dict(name="the_row", type="float64", is_const=True, is_list=True),
                        ],
                    )
                ],
                members=[dict(name="the_list", type="string", is_list=True, is_const=True)],
            )
        ],
    )


#
# tests
#


def test_swift_binding_generator_minimal(api_minimal_valid: dict):
    hdr_ctx, src_ctx = SwiftBindingGenerator(
        ApiDef(**api_minimal_valid), gen_version="test-0.0.0", api_h="test_api.h"
    ).generate_ctx(hdr=Path("unused_umbrella.h"), src=Path("unused_bindings.cpp"))
    assert hdr_ctx.line_count > 1
    assert src_ctx.line_count > 1
    lines = hdr_ctx.lines
    lines = src_ctx.lines


def test_swift_binding_generator_list_member(api_with_list: dict):
    hdr_ctx, src_ctx = SwiftBindingGenerator(
        ApiDef(**api_with_list), gen_version="test-0.0.0", api_h="test_api.h"
    ).generate_ctx(hdr=Path("unused_umbrella.h"), src=Path("unused_bindings.cpp"))
    assert hdr_ctx.line_count > 1
    assert src_ctx.line_count > 1
    lines = hdr_ctx.lines
    lines = src_ctx.lines


def test_swift_generator_minimal(api_minimal_valid: dict):
    _, src_ctx = SwiftGenerator(
        ApiDef(**api_minimal_valid), gen_version="test-0.0.0", api_h="api_umbrella.h"
    ).generate_ctx(src=Path("unused.swift"))
    assert src_ctx.line_count > 1
    lines = src_ctx.lines


def test_swift_generator_list_member(api_with_list: dict):
    _, src_ctx = SwiftGenerator(
        ApiDef(**api_with_list), gen_version="test-0.0.0", api_h="api_umbrella.h"
    ).generate_ctx(src=Path("unused.swift"))
    assert src_ctx.line_count > 1
    lines = src_ctx.get_gen_text()
