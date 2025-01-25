#!/usr/bin/env python3
from pathlib import Path
import sys
import cyclopts

sys.path.append((Path(__file__).parent / "code_gen").as_posix())

from api_def import ApiDef
from cpp_generator import CppGenerator
from c_generator import CBindingGenerator
from kotlin_generator import (JniBindingGenerator, KtGenerator)
from swift_generator import (SwiftBindingGenerator, SwiftGenerator)
from wasm_generator import (WasmBindingGenerator, JSGenerator)

gen_api_version = "0.5.0"

app = cyclopts.App(
    version=gen_api_version,
    name=Path(__file__).name
)

@app.command
def generate_cpp_interface(*, api_def: Path, out_h: Path):
    """
    generates C++ interface header for author to implement

    Parameters
    ----------
    api_def
        api definition json
    out_h
        output path for generated interface header
    """
    CppGenerator(ApiDef.from_file(api_def)).generate_files(hdr=out_h)

@app.command
def generate_c_wrapper(*, api_def: Path, api_h: str, out_h: Path, out_cpp: Path):
    """
    generates C wrapper API header with extern C implementation cpp file

    Parameters
    ----------
    api_def
        api definition json
    api_h
        dependency interface header from generate_cpp_interface
    out_h
        output path for generated wrapper header
    out_cpp
        output path for generated wrapper source
    """
    CBindingGenerator(ApiDef.from_file(api_def), api_h=api_h).generate_files(hdr=out_h, src=out_cpp)

@app.command
def generate_jni_binding(*, api_def: Path, api_h: str, api_pkg: str, out_cpp: Path):
    """
    generates JNI binding code

    Parameters
    ----------
    api_def
        api definition json
    api_h
        dependency interface header from generate_cpp_interface
    api_pkg
        name of kotlin package (e.g. com.company.library)
    out_cpp
        output path for generated JNI cpp sourcer
    """
    JniBindingGenerator(ApiDef.from_file(api_def), api_h=api_h, api_pkg=api_pkg).generate_files(src=out_cpp)

@app.command
def generate_kt_wrapper(*, api_def: Path, out_kt: Path):
    """
    command line utility for capturing web client composition renders

    Parameters
    ----------
    api_def
        api definition json
    out_kt
        output path for generated kotlin wrapper
    """
    KtGenerator(ApiDef.from_file(api_def)).generate_files(src=out_kt)

@app.command
def generate_swift_binding(
        *,
        api_def: Path,
        api_h: str,
        out_h: Path,
        out_cpp: Path
):
    """
    command line utility for capturing web client composition renders

    Parameters
    ----------
    api_def
        api definition json
    api_h
        dependency interface header from generate_cpp_interface
    out_h
        output path for generated binding header
    out_cpp
        output path for generated binding implementation
    """
    SwiftBindingGenerator(ApiDef.from_file(api_def), api_h=api_h).generate_files(hdr=out_h, src=out_cpp)

@app.command
def generate_swift_wrapper(*, api_def: Path, swift_h: str, out_swift: Path):
    """
    command line utility for capturing web client composition renders

    Parameters
    ----------
    api_def
        api definition json
    swift_h
       dependency import header from generate_swift_binding
    out_swift
        output path for generated swift wrapper
    """
    SwiftGenerator(ApiDef.from_file(api_def), api_h=swift_h).generate_files(src=out_swift)

@app.command
def generate_wasm_binding(
        *,
        api_def: Path,
        api_h: str,
        out_cpp: Path,
):
    """
    command line utility for capturing web client composition renders

    Parameters
    ----------
    api_def
        api definition json
    api_h
        dependency interface header from generate_cpp_interface
    out_cpp
        output path for generated cpp wasm binding
    """
    WasmBindingGenerator(ApiDef.from_file(api_def), api_h=api_h).generate_files(src=out_cpp)

@app.command
def generate_js_wrapper(
        *,
        api_def: Path,
        out_js: Path
):
    """
    command line utility for capturing web client composition renders

    Parameters
    ----------
    api_def
        api definition json
    out_js
        output path for generated javascript wrapper
    """
    JSGenerator(ApiDef.from_file(api_def)).generate_files(src=out_js)

if __name__ == "__main__":
    app()
