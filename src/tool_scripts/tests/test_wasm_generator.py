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
from wasm_generator import WasmBindingGenerator

#
# fixtures
#
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
                       type="float64", name="list_sum",
                       parameters=[
                           dict(name="label", type="string", is_const=True),
                           dict(name="the_row", type="float64", is_const=True, is_list=True)
                       ]
                    )
                 ],
                 members=[
                     dict(name="the_list", type="string", is_list=True, is_const=True)
                 ]
            )
        ]
    )

#
# tests
#

def test_wasm_binding_gen(api_with_list: dict):
    _, src_ctx = WasmBindingGenerator(
        ApiDef(**api_with_list),
        gen_version="test-0.0.0",
        api_h="test_api.h"
    ).generate_ctx(src=Path("unused.cpp"))
    lines = src_ctx.get_gen_text()
    assert "class_<TheClass>(\"TheClass\")" in lines
