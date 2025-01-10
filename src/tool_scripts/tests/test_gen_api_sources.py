#!/usr/bin/env python3
from pathlib import Path

from _pytest.fixtures import fixture

TOOLS_DIR = Path(__file__).parent.parent.absolute()
TESTS_DIR = Path(__file__).parent.absolute()
OUT_DIR = TESTS_DIR / "test_output"

from gen_api_sources import (
    Named,
    TypedNamed,
    BaseType,
    PrimitiveType,
    ConstantDef,
    EnumDef,
    AliasDef,
    MemberDef,
    StructDef,
    ParameterDef,
    MethodDef,
    ClassDef,
    FunctionDef,
    ApiDef,
    GenCtx,
    CppGenerator,
    CBindingsGenerator,
    WasmBindingGenerator,
    JSGenerator,
    JniBindingGenerator,
    KtGenerator,
    SwiftBindingGenerator,
    SwiftGenerator,
    generate,
    get_type,
    init_type_table,
    reset_type_table,
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
    assert False

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
    init_type_table()
    try:
        ApiDef(**api_no_api)
    except ValueError as ve:
        return
    # should throw when no api guts are defined
    assert False

def test_api_minimal_valid(api_minimal_valid: dict):
    init_type_table()
    ApiDef(**api_minimal_valid)

def test_cpp_generator_minimal(api_minimal_valid: dict):
    init_type_table()
    timestamp = f"right about now."
    hdr_ctx, src_ctx = CppGenerator(timestamp).generate_api_ctx(ApiDef(**api_minimal_valid))
    assert hdr_ctx.line_count > 1
    lines = hdr_ctx.lines
    assert "  static constexpr int32_t the_const = 1;" in lines
    assert "namespace test::api {" in lines

def test_cpp_generator_list_member():


def test_integrated_api0():
    generate(
        api_def=TESTS_DIR / "api0_def.json",
        c_dir=OUT_DIR / "c",
        cpp_dir=OUT_DIR / "cpp",
        wasm_binding_dir=OUT_DIR / "wasm_bindings",
        js_dir=OUT_DIR / "js",
        jni_binding_dir=OUT_DIR / "jni_bindings",
        kotlin_dir=OUT_DIR / "kotlin",
        swift_binding_dir=OUT_DIR / "swift_bindings",
        swift_dir=OUT_DIR / "swift"
    )

def test_integrated_api1():
    generate(
        api_def=TESTS_DIR / "api1_def.json",
        c_dir=OUT_DIR / "c",
        cpp_dir=OUT_DIR / "cpp",
        wasm_binding_dir=OUT_DIR / "wasm_bindings",
        js_dir=OUT_DIR / "js",
        jni_binding_dir=OUT_DIR / "jni_bindings",
        kotlin_dir=OUT_DIR / "kotlin",
        swift_binding_dir=OUT_DIR / "swift_bindings",
        swift_dir=OUT_DIR / "swift"
    )
