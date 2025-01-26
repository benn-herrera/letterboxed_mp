from pathlib import Path
import sys
from _pytest.fixtures import fixture

TESTS_DIR = Path(__file__).parent
TOOLS_DIR = TESTS_DIR.parent
CODE_GEN_DIR = TOOLS_DIR / "code_gen"
OUT_DIR = TESTS_DIR / "test_output"

sys.path.append(TOOLS_DIR.as_posix())
sys.path.append(CODE_GEN_DIR.as_posix())

# noinspection PyUnresolvedReferences
from api_def import (
    Named,
    TypedNamed,
    BaseType,
    ApiDef,
    init_type_table,
    reset_type_table,
    get_type,
)
# noinspection PyUnresolvedReferences
from cpp_generator import CppGenerator
#from c_generator import CBindingGenerator
# noinspection PyUnresolvedReferences
from wasm_generator import WasmBindingGenerator
#from kotlin_generator import (JniBindingGenerator, KtGenerator)
#from swift_generator import (SwiftBindingGenerator, SwiftGenerator)
# noinspection PyUnresolvedReferences
from gen_api_sources import (
    generate_cpp_interface,
    generate_c_wrapper,
    generate_jni_binding,
    generate_kt_wrapper,
    generate_swift_binding,
    generate_swift_wrapper,
    generate_wasm_binding
)

#
# fixtures
#

@fixture
def api_no_api() -> dict:
    return dict(
        name="test_api",
        version="1.2.3"
    )

@fixture
def api_minimal_valid() -> dict:
    return dict(
        name="test_api",
        version="1.2.3",
        constants=[
            dict(
                type="int32",
                name="the_const",
                value="1"
            )
        ]
    )

#
# tests
#

def test_correct_usage():
    n = Named(name="norman")
    assert n.name == "norman"

def test_required_attr():
    try:
        Named()
    except ValueError as ve:
        return
    # should have thrown because name="foo" missing
    assert False

def test_unhandled_attr():
    try:
        Named(name="foo", unhandled="bar")
    except ValueError as ve:
        return
    # should have thrown because unhandled is not a valid attribute
    assert False

def test_type_registration():
    reset_type_table()
    bt = BaseType(name="the_type_name")
    assert bt is get_type(bt.name)

    reset_type_table()
    try:
        get_type(bt.name)
    except ValueError as ve:
        return
    # type should not be in table
    assert False

def test_init_primitive_types():
    init_type_table()
    get_type("int32")
    get_type("bool")
    get_type("string")
    get_type("float64")
    reset_type_table()

def test_optional_attr():
    # is_const optional - specified
    reset_type_table()
    BaseType(name="the_type_name")
    tn = TypedNamed(name="the_var_name", type="the_type_name", is_const=True)
    assert tn.name == "the_var_name" and tn.type == "the_type_name" and tn.is_const == True
    # is_const not specified. should be fine.
    tn = TypedNamed(name="the_var_name", type="the_type_name")
    assert tn.name == "the_var_name" and tn.type == "the_type_name" and tn.is_const == False

def test_validation():
    reset_type_table()
    BaseType(name="the_type_name")
    try:
        TypedNamed(name="the_var_name", type="the_type_name", is_list=True, is_array=True)
    except ValueError as ve:
        return
    # is_list and is_array should fail validation as mutually exclusive
    assert False

def test_api_no_api(api_no_api: dict):
    try:
        ApiDef(**api_no_api)
    except ValueError as ve:
        return
    # should throw when no api guts are defined
    assert False

def test_api_minimal_valid(api_minimal_valid: dict):
    api = ApiDef(**api_minimal_valid)
    assert api.name == "test_api"
    assert api.version == "1.2.3"

def test_assign_float_to_int():
    try:
        ApiDef(
            name="test_api",
            version="1.2.3",
            constants=[
                dict(
                    type="int32",
                    name="the_const",
                    value=1.5
                )
            ]
        )
    except ValueError as ve:
        return
    # should have thrown for assigning 1.5 to int value
    assert False

def test_cpp_generator_minimal(api_minimal_valid: dict):
    api = ApiDef(**api_minimal_valid)
    hdr_ctx, _ = CppGenerator(
        api,
        gen_version="test-0.0.0",
        use_std=False
    ).generate_ctx(hdr=Path("unused.h"), src=None)
    assert hdr_ctx.line_count > 1
    lines = hdr_ctx.lines
    assert "  static constexpr int32_t the_const = 1;" in lines
    assert "namespace test::api {" in lines

def test_cpp_generator_list_member():
    api = ApiDef(
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
    hdr_ctx, _ = CppGenerator(
        api,
        gen_version="test-0.0.0",
        use_std=True
    ).generate_ctx(hdr=Path("unused.h"))
    lines = hdr_ctx.get_gen_text()
    assert "the_list_count" not in lines
    assert "const std::vector<double>& the_row) = 0;" in lines
    assert "std::vector<std::string> the_list;" in lines

    hdr_ctx, _ = CppGenerator(
        api,
        gen_version="test-0.0.0",
        use_std=False).generate_ctx(hdr=Path("unused.h"))
    lines = hdr_ctx.get_gen_text()
    assert "const double* the_row, " in lines
    assert "int32_t the_row_count) = 0;" in lines
    assert "int32_t the_list_count;" in lines
    assert "const char** the_list;" in lines

def test_wasm_binding_gen():
    api = ApiDef(
        name="test_api",
        version="1.2.3",
        classes=[
            dict(
                name="TheClass",
                methods=[
                    dict(
                        type="TheClass", name="create", is_reference=True, is_static=True, is_factory=True
                    ),
                    dict(
                       type="float64", name="list_sum",
                       parameters=[
                           dict(name="label", type="string", is_const=True),
                           dict(name="the_row", type="float64", is_const=True, is_list=True)
                       ]
                    )
                 ]
            )
        ]
    )
    _, src_ctx = WasmBindingGenerator(
        api,
        gen_version="test-0.0.0",
        api_h="test_api.h"
    ).generate_ctx(src=Path("unused.cpp"))
    lines = src_ctx.get_gen_text()
    assert "class_<TheClass>(\"TheClass\")" in lines

def test_integrated_api0():
    idx = 0
    api_def = TESTS_DIR / f"api{idx}_def.json"
    api_h = OUT_DIR / f"api_{idx}.h"
    swift_h = OUT_DIR / f"swift_binding_{idx}.h"

    generate_cpp_interface(api_def=api_def, out_h=api_h)
    generate_c_wrapper(
        api_def=api_def, api_h=api_h.name,
        out_h=OUT_DIR / f"c_wrapper_{idx}.h", out_cpp=OUT_DIR / f"c_wrapper_{idx}.cpp")
    generate_jni_binding(
        api_def=api_def, api_h=api_h.name, api_pkg="com.tinybitsinteractive.lbsolverlib.nativecore",
        out_cpp=OUT_DIR / f"jni_binding_{idx}.cpp")
    generate_kt_wrapper(api_def=api_def, out_kt=OUT_DIR / f"kotlin_wrapper_{idx}.kt")
    generate_swift_binding(
        api_def=api_def, api_h=api_h.name,
        out_h=swift_h, out_cpp=OUT_DIR / f"swift_binding_{idx}.cpp")
    generate_swift_wrapper(
        api_def=api_def, swift_h=swift_h.name,
        out_swift=OUT_DIR / f"swift_wrapper_{idx}.swift")
    generate_wasm_binding(
        api_def=api_def, api_h=api_h.name,
        out_cpp=OUT_DIR / f"wasm_binding_{idx}.cpp")

def test_integrated_api1():
    idx = 1
    api_def = TESTS_DIR / f"api{idx}_def.json"
    api_h = OUT_DIR / f"api_{idx}.h"
    swift_h = OUT_DIR / f"swift_binding_{idx}.h"

    generate_cpp_interface(api_def=api_def, out_h=api_h)
    generate_c_wrapper(
        api_def=api_def, api_h=api_h.name,
        out_h=OUT_DIR / f"c_wrapper_{idx}.h", out_cpp=OUT_DIR / f"c_wrapper_{idx}.cpp")
    generate_jni_binding(
        api_def=api_def, api_h=api_h.name, api_pkg="com.tinybitsinteractive.lbsolverlib.nativecore",
        out_cpp=OUT_DIR / f"jni_binding_{idx}.cpp")
    generate_kt_wrapper(api_def=api_def, out_kt=OUT_DIR / f"kotlin_wrapper_{idx}.kt")
    generate_swift_binding(
        api_def=api_def, api_h=api_h.name,
        out_h=swift_h, out_cpp=OUT_DIR / f"swift_binding_{idx}.cpp")
    generate_swift_wrapper(
        api_def=api_def, swift_h=swift_h.name,
        out_swift=OUT_DIR / f"swift_wrapper_{idx}.swift")
    generate_wasm_binding(
        api_def=api_def, api_h=api_h.name,
        out_cpp=OUT_DIR / f"wasm_binding_{idx}.cpp")
