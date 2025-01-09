#!/usr/bin/env python3
import glob
from codecs import ignore_errors
from pathlib import Path
import sys

TOOLS_DIR = Path(sys.argv[0]).parent.parent.absolute()
TESTS_DIR = Path(sys.argv[0]).parent.absolute()
OUT_DIR = TESTS_DIR / "test_output"

sys.path.append(TOOLS_DIR.as_posix())
from gen_api_sources import generate

for def_file in sorted(list(glob.glob(f"{TESTS_DIR}/*.json"))):
    def_path = Path(def_file)
    print(f"testing {def_path.name}...", end="", flush=True)
    try:
        generate(
            api_def=def_path,
            c_dir=OUT_DIR / "c",
            cpp_dir=OUT_DIR / "cpp",
            wasm_binding_dir=OUT_DIR / "wasm_bindings",
            js_dir=OUT_DIR / "js",
            jni_binding_dir=OUT_DIR / "jni_bindings",
            kotlin_dir=OUT_DIR / "kotlin",
            swift_binding_dir=OUT_DIR / "swift_bindings",
            swift_dir=OUT_DIR / "swift"
        )
    except Exception as ex:
        print(f"FAILED.", flush=True)
        print(f"{ex}", file=sys.stderr)
        continue
    print("passed.")
