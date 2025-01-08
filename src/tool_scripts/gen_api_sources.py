#!/usr/bin/env python3
import os
import sys
import time
from datetime import datetime
from typing import Optional

import cyclopts
import json
from pathlib import Path

gen_api_version = "0.5.0"

PROJECT_DIR = Path(sys.argv[0]).parent.parent.parent.absolute()
DEF_DIR = PROJECT_DIR / "src/api"
CPP_SRC_DIR = PROJECT_DIR / "src"
CPP_PLATFORM_DIR = CPP_SRC_DIR / "platform"
KOTLIN_SRC_DIR = PROJECT_DIR / "kotlin_project"
SWIFT_SRC_DIR = PROJECT_DIR / "swift_project"
JS_SRC_DIR = PROJECT_DIR / "wasm_project"

TEST_HACK_MODE = True
# TEST HACK
if TEST_HACK_MODE:
    PROJECT_DIR = PROJECT_DIR / "build_desktop/gen_test"
    CPP_SRC_DIR = PROJECT_DIR / "src"
    CPP_PLATFORM_DIR = CPP_SRC_DIR / "platform"
    KOTLIN_SRC_DIR = PROJECT_DIR / "kotlin_project"
    SWIFT_SRC_DIR = PROJECT_DIR / "swift_project"
    JS_SRC_DIR = PROJECT_DIR / "wasm_project"

SCRIPT_NAME = f"{Path(sys.argv[0]).name}"

app = cyclopts.App(
    version=gen_api_version,
    name=SCRIPT_NAME
)

def _snake_to_camel(val: str) -> str:
    return ''.join([(s.capitalize() if i > 0 else s) for (i, s) in enumerate(str.split('_'))])

def _is_public_data_member(obj, field: str, value) -> bool:
    return (not field.startswith("_")) and (not callable(value))

def _init_obj_from_dict(obj, dct: dict):
    dct_keys = set(dct.keys())
    unset_attrs = set()
    for field in [field for (field, value) in obj.__dict__.items() if _is_public_data_member(obj, field, value)]:
        if field in dct:
            setattr(obj, field, dct.get(field))
            dct_keys.remove(field)
        else:
            if callable(getattr(obj, "is_attr_optional", None)):
                if obj.is_attr_optional(field):
                    continue
            unset_attrs.add(field)
    err_msgs = []
    if dct_keys:
        err_msgs.append(f"{dct_keys} are not attributes of {obj.__class__.__name__} {getattr(obj, 'name', '')}")
    if unset_attrs:
        err_msgs.append(f"{unset_attrs} are required attributes of {obj.__class__.__name__} {getattr(obj, 'name', '')} but were not set")
    if err_msgs:
        raise ValueError("\n".join(err_msgs))


class Named:
    def __init__(self, name: Optional[str]=None):
        self.name: Optional[str] = name

    def __str__(self):
        return f"{self.name}{{{self.__class__.__name__}}}"


class BaseType(Named):
    def __init__(self, name: str, *, language_table: Optional[dict] = None):
        super().__init__(name)
        self.type = name
        self.language_table = language_table if language_table else {}

    @property
    def is_int(self):
        return "int" in self.name

    @property
    def is_float(self):
        return "float" in self.name

    @property
    def is_number(self):
        return self.is_int or self.is_float

    @property
    def type_obj(self):
        return self

    @property
    def resolved_type_obj(self):
        return self


_type_table = {}

def _add_type(typ: Named):
    if typ.name in _type_table:
        raise ValueError(f"{typ.name} already defined as {_type_table[typ.name]}, can't redefine as {typ}")
    _type_table[typ.name] = typ

def _get_type(name: str, *, is_void_legal: bool = False):
    if name not in _type_table:
        raise ValueError(f"type {name} is not in the type table")
    t = _type_table[name]
    if (not is_void_legal) and (t.name == "void"):
        raise ValueError(f"{t} is not legal here.")
    return t


class Typed(Named):
    def __init__(self, *, is_void_legal: bool = False):
        self.type: Optional[str] = None
        self._is_void_legal = is_void_legal
        super().__init__()

    @property
    def type_obj(self):
        return _get_type(self.type, is_void_legal = self._is_void_legal)

    @property
    def resolved_type_obj(self):
        return self.type_obj

    def __str__(self):
        return f"{self.name}: {self.type_obj}"


class ConstantDef(Typed):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.value = None
        if dct:
            _init_obj_from_dict(self, dct)
            ct = self.resolved_type_obj
            if not ct.is_number:
                raise ValueError(f"{self} type {ct} is not numeric.")


class EnumValue(Named):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.value = None
        if dct:
            _init_obj_from_dict(self, dct)


class EnumDef(Typed):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.members = []
        if dct:
            _init_obj_from_dict(self, dct)
            self.members = [EnumValue(m) for m in self.members]
            _add_type(self)
            et = self.resolved_type_obj
            if not et.is_int:
                raise ValueError(f"{self} type {et} is not integral.")


class AliasDef(Typed):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        if dct:
            _init_obj_from_dict(self, dct)
            _add_type(self)

    @property
    def resolved_type_obj(self):
        rt = self
        while isinstance(rt, AliasDef):
            rt = self.type_obj
        return rt


class MemberDef(Typed):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.array_count = None
        if dct:
            _init_obj_from_dict(self, dct)
            _ = self.type_obj

    def is_attr_optional(self, attr_name: str) -> bool:
        if not attr_name in self.__dict__:
            raise ValueError(f"{attr_name} is not an attribute of {self} ")
        return attr_name in ["array_count"]


class StructDef(Named):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.members = []
        if dct:
            _init_obj_from_dict(self, dct)
            _add_type(self)
            self.members = [MemberDef(m) for m in self.members]


class ParameterDef(Typed):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        if dct:
            _init_obj_from_dict(self, dct)
            _ = self.type_obj


class MethodDef(Typed):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__(is_void_legal=True)
        self.parameters = []
        self.is_static = False
        if dct:
            _init_obj_from_dict(self, dct)
            _ = self.type_obj
            self.parameters = [ParameterDef(p) for p in self.parameters]

    def is_attr_optional(self, attr_name: str) -> bool:
        if not attr_name in self.__dict__:
            raise ValueError(f"{attr_name} is not an attribute of {self} ")
        return attr_name in ["is_static"]


class ClassDef(Named):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.members = []
        self.methods = []
        if dct:
            _init_obj_from_dict(self, dct)
            _add_type(self)
            self.members = [MemberDef(m) for m in self.members]
            self.methods = [MethodDef(m) for m in self.methods]


class FunctionDef(Typed):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__(is_void_legal=True)
        self.parameters = []
        if dct:
            _init_obj_from_dict(self, dct)
            _ = self.type_obj
            self.parameters = [ParameterDef(p) for p in self.parameters]


class ApiDef(Named):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.version: Optional[str] = None
        self.aliases = []
        self.classes = []
        self.constants = []
        self.enums = []
        self.functions = []
        self.structs = []
        if dct:
            _init_obj_from_dict(self, dct)
            self.constants = [ConstantDef(c) for c in self.constants]
            self.enums = [EnumDef(e) for e in self.enums]
            self.aliases = [AliasDef(o) for o in self.aliases]
            self.structs = [StructDef(s) for s in self.structs]
            self.classes = [ClassDef(s) for s in self.classes]
            self.functions = [FunctionDef(f) for f in self.functions]

    def is_attr_optional(self, attr_name: str) -> bool:
        if not attr_name in self.__dict__:
            raise ValueError(f"{attr_name} is not an attribute of {self} ")
        return attr_name in ["aliases", "classes", "constants", "enums", "functions", "structs"]

class GenCtx:
    def __init__(self):
        self.indent_count = 0
        self.ctx_stack = []
        self.lines = []

    @property
    def indentation(self):
        return "  " * self.indent_count if self.indent_count > 0 else ""

    def push_indent(self):
        self.indent_count += 1

    def pop_indent(self):
        if self.indent_count == 0:
            raise Exception("can't reduce indent below 0")
        self.indent_count -= 1

    def push_ctx(self, ctx):
        self.ctx_stack.append(ctx)

    def pop_ctx(self):
        if not self.ctx_stack:
            raise Exception("ctx stack is empty")
        self.ctx_stack.pop(-1)

    def add_lines(self, lines):
        if isinstance(lines, str):
            lines = lines.split('\n')
        elif isinstance(lines, list) and isinstance(lines[0], str):
            pass
        else:
            raise ValueError(f"{lines} is not a string or string list")
        self.lines.extend([f"{self.indentation}{ln}" for ln in lines])

    @property
    def ctx(self):
        if not self.ctx_stack:
            raise Exception("ctx stack is empty")
        return self.ctx_stack[-1]

    def get_gen_text(self) -> str:
        # maybe error check state of ctx here
        return "\n".join(self.lines) + "\n"


class Language:
    def __init__(self):
        pass

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def sfx(self):
        return "." + self.name[:-len("Language")].lower()

    def _comment(self, text: str) -> [str]:
        raise Exception(f"_comment not implemented in {self.name}")

    def _generate_api_lines(self, api: ApiDef, *, ctx: GenCtx):
        raise Exception(f"generate_api_lines not implemented in {self.name}")

    def generate_api(self, api: ApiDef, out_dir: Path):
        out_path = out_dir / f"{api.name}{self.sfx}"
        ctx = GenCtx()
        ctx.add_lines(self._comment(f"{out_path.name} generated by {SCRIPT_NAME} {datetime.now()}"))
        self._generate_api_lines(api, ctx=ctx)
        out_path.write_text(ctx.get_gen_text(), encoding="utf-8", newline="\n")


class CLanguage(Language):
    def __init__(self):
        super().__init__()

    def _comment(self, text: str) -> [str]:
        return [f"/* {ln} */" for ln in text.split("\n")]

    def _generate_api_lines(self, api: ApiDef, ctx: GenCtx):
        ctx.add_lines("#pragma once // C")

class CppLanguage(Language):
    def __init__(self):
        super().__init__()

    def _comment(self, text: str) -> [str]:
        return [f"// {ln}" for ln in text.split("\n")]

    def _generate_api_lines(self, api: ApiDef, ctx: GenCtx):
        ctx.add_lines("#pragma once // CPP")


class WasmBindingLanguage(CppLanguage):
    def __init__(self):
        super().__init__()

    def _generate_api_lines(self, api: ApiDef, ctx: GenCtx):
        ctx.add_lines("#pragma once // WASM BINDING")

    @property
    def sfx(self):
        return ".cpp"


class JSLanguage(Language):
    def __init__(self):
        super().__init__()

    _comment = CLanguage._comment

    def _generate_api_lines(self, api: ApiDef, ctx: GenCtx):
        ctx.add_lines("// JS BINDING")


class JniBindingLanguage(CppLanguage):
    def __init__(self):
        super().__init__()

    def _generate_api_lines(self, api: ApiDef, ctx: GenCtx):
        ctx.add_lines("#pragma once // JNI BINDING")

    @property
    def sfx(self):
        return ".cpp"


class KtLanguage(Language):
    def __init__(self):
        super().__init__()

    _comment = CppLanguage._comment

    def _generate_api_lines(self, api: ApiDef, ctx: GenCtx):
        ctx.add_lines("import com.google.android.foo")

class SwiftBindingLanguage(CLanguage):
    def __init__(self):
        super().__init__()

    def _generate_api_lines(self, api: ApiDef, ctx: GenCtx):
        ctx.add_lines("#pragma once // SWIFT BINDING")

    @property
    def sfx(self):
        return ".cpp"


class SwiftLanguage(Language):
    def __init__(self):
        super().__init__()

    _comment = CppLanguage._comment

    def _generate_api_lines(self, api: ApiDef, ctx: GenCtx):
        ctx.add_lines("import Foundation")


def _init_type_table():
    base_types = [
        "void",
        "bool",
        "int8",
        "uint8",
        "int16",
        "uint16",
        "int32",
        "uint32",
        "int64",
        "uint64",
        "intptr",
        "float32",
        "float64",
        "string",
        "const_string"
    ]
    for base_type in base_types:
        _add_type(BaseType(base_type))

def gen_c_header(api_def: ApiDef, c_dir: Path):
    os.makedirs(c_dir.as_posix(), exist_ok=True)
    CLanguage().generate_api(api_def, c_dir)

def gen_cpp_header(api_def: ApiDef, cpp_dir: Path):
    os.makedirs(cpp_dir.as_posix(), exist_ok=True)
    CppLanguage().generate_api(api_def, cpp_dir)

def gen_wasm_binding(api_def: ApiDef, wasm_binding_dir: Path):
    os.makedirs(wasm_binding_dir.as_posix(), exist_ok=True)
    WasmBindingLanguage().generate_api(api_def, wasm_binding_dir)

def gen_js(api_def: ApiDef, js_dir: Path):
    os.makedirs(js_dir.as_posix(), exist_ok=True)
    JSLanguage().generate_api(api_def, js_dir)

def gen_jni_binding(api_def: ApiDef, jni_binding_dir: Path):
    os.makedirs(jni_binding_dir.as_posix(), exist_ok=True)
    JniBindingLanguage().generate_api(api_def, jni_binding_dir)

def gen_kotlin(api_def: ApiDef, kotlin_dir: Path):
    os.makedirs(kotlin_dir.as_posix(), exist_ok=True)
    KtLanguage().generate_api(api_def, kotlin_dir)

def gen_swift_binding(api_def: ApiDef, swift_binding_dir: Path):
    os.makedirs(swift_binding_dir.as_posix(), exist_ok=True)
    SwiftBindingLanguage().generate_api(api_def, swift_binding_dir)

def gen_swift(api_def: ApiDef, swift_dir: Path):
    os.makedirs(swift_dir.as_posix(), exist_ok=True)
    SwiftLanguage().generate_api(api_def, swift_dir)

@app.default
def generate(
        api_def: Path = DEF_DIR / "api_def.json",
        c_dir: Path = CPP_SRC_DIR / "api",
        cpp_dir: Path = CPP_SRC_DIR / "engine",
        wasm_binding_dir: Path = CPP_PLATFORM_DIR / "wasm",
        js_dir = JS_SRC_DIR / "modules",
        jni_binding_dir: Path = CPP_PLATFORM_DIR / "mobile/android",
        kotlin_dir: Path = KOTLIN_SRC_DIR / "lbsolverlib/src/main/kotlin/com/tinybitsinteractive/lbsolverlib/nativecore",
        swift_binding_dir: Path = CPP_PLATFORM_DIR / "mobile/ios",
        swift_dir: Path = SWIFT_SRC_DIR / "lbsolverlib/Sources/lbsolverlib"
):
    """
    command line utility for capturing web client composition renders

    Parameters
    ----------
    api_def
        path to .json file with API definition
    c_dir
        directory for generated pure c
    cpp_dir
        directory for generated c++
    wasm_binding_dir
        directory for generated wasm binding code
    js_dir
        directory for generated javascript
    jni_binding_dir
        directory for generated jni bindings
    kotlin_dir
        directory for generated kotlin
    swift_binding_dir
        directory for generated swift bindings
    swift_dir
        directory for generated swift
    """
    _init_type_table()

    api_def = ApiDef(json.loads(api_def.read_text(encoding="utf8")))

    gen_c_header(api_def, c_dir)
    gen_cpp_header(api_def, cpp_dir)
    gen_wasm_binding(api_def, wasm_binding_dir)
    gen_js(api_def, js_dir)
    gen_jni_binding(api_def, jni_binding_dir)
    gen_kotlin(api_def, kotlin_dir)
    gen_swift_binding(api_def, swift_binding_dir)
    gen_swift(api_def, swift_dir)

if __name__ == "__main__":
    app()
