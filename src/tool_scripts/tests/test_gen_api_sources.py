import sys
from pathlib import Path
# from _pytest.fixtures import fixture

TESTS_DIR = Path(__file__).parent
TOOLS_DIR = TESTS_DIR.parent
CODE_GEN_DIR = TOOLS_DIR / "code_gen"
OUT_DIR = TESTS_DIR / "test_output"

sys.path.append(TOOLS_DIR.as_posix())
sys.path.append(CODE_GEN_DIR.as_posix())

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

#
# tests
#

def test_integrated_api0():
    idx = 0
    api_def = TESTS_DIR / f"fixtures/api{idx}_def.json"
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
    api_def = TESTS_DIR / f"fixtures/api{idx}_def.json"
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
