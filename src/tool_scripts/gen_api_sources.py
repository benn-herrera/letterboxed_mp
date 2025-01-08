#!/usr/bin/env python3
import os
import sys
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
TIMESTAMP = datetime.now()

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
        self._indent_count = 0
        self._ctx_stack = []
        self._lines = []

    @property
    def indentation(self):
        return "  " * self._indent_count if self._indent_count > 0 else ""

    def push_indent(self):
        self._indent_count += 1

    def pop_indent(self):
        if self._indent_count == 0:
            raise Exception("can't reduce indent below 0")
        self._indent_count -= 1

    def push_ctx(self, ctx):
        self._ctx_stack.append(ctx)

    def pop_ctx(self):
        if not self._ctx_stack:
            raise Exception("ctx stack is empty")
        self._ctx_stack.pop(-1)

    def add_lines(self, lines):
        if isinstance(lines, str):
            lines = lines.split('\n')
        elif isinstance(lines, list) and isinstance(lines[0], str):
            pass
        else:
            raise ValueError(f"{lines} is not a string or string list")
        self._lines.extend([f"{self.indentation}{ln}" for ln in lines])

    @property
    def line_count(self):
        return len(self._lines)

    @property
    def ctx(self):
        if not self._ctx_stack:
            raise Exception("ctx stack is empty")
        return self._ctx_stack[-1]

    def get_gen_text(self) -> str:
        if self._ctx_stack or self._indent_count > 0:
            raise Exception("indent and/or context stack have more pushes than pops")
        return "\n".join(self._lines) + "\n"


class Generator:
    _hdr_sfx = None
    _src_sfx = None

    def __init__(self):
        pass

    @property
    def name(self):
        return self.__class__.__name__

    def _header_name(self, api: ApiDef) -> Optional[str]:
        return f"{api.name}{self._hdr_sfx}" if self._hdr_sfx else None

    def _src_name(self, api: ApiDef) -> Optional[str]:
        return f"{api.name}{self._src_sfx}" if self._src_sfx else None

    def _comment(self, text: str) -> [str]:
        raise Exception(f"_comment not implemented in {self.name}")

    def _generate_api(self, api: ApiDef, *, src_ctx: GenCtx, hdr_ctx: Optional[GenCtx]):
        raise Exception(f"_generate_api not implemented in {self.name}")

    def generate_api(self, api: ApiDef, out_dir: Path):
        src_out_path = None
        src_ctx = None
        hdr_out_path = None
        hdr_ctx = None

        os.makedirs(out_dir.as_posix(), exist_ok=True)

        if self._hdr_sfx:
            hdr_ctx = GenCtx()
            hdr_out_path = out_dir / self._header_name(api)
            hdr_ctx.add_lines(self._comment(f"{hdr_out_path.name} generated by {SCRIPT_NAME} {TIMESTAMP}"))

        if self._src_sfx:
            src_ctx = GenCtx()
            src_out_path = out_dir / self._src_name(api)
            src_ctx.add_lines(self._comment(f"{src_out_path.name} generated by {SCRIPT_NAME} {TIMESTAMP}"))

        if not (src_ctx or hdr_ctx):
            raise Exception(f"{self.name} does not not have valid _src_sfx or _hdr_sfx")

        self._generate_api(api, src_ctx=src_ctx, hdr_ctx=hdr_ctx)

        if hdr_ctx and (hdr_ctx.line_count > 1):
            hdr_out_path.write_text(hdr_ctx.get_gen_text(), encoding="utf-8", newline="\n")

        if src_ctx and (src_ctx.line_count > 1):
            src_out_path.write_text(src_ctx.get_gen_text(), encoding="utf-8", newline="\n")


class CppGenerator(Generator):
    _hdr_sfx = ".h"

    def __init__(self):
        super().__init__()

    def _comment(self, text: str) -> [str]:
        return [f"// {ln}" for ln in text.split("\n")]

    def _if_def(self, symbol: str, *, ctx: GenCtx):
        ctx.add_lines(f"#if defined({symbol})")

    def _endif_def(self, symbol: str, *, ctx: GenCtx):
        ctx.add_lines(f"#endif // defined({symbol})")

    def _ifdef(self, symbol: str, *, body, ctx: GenCtx):
        self._if_def(symbol, ctx=ctx)
        ctx.add_lines(body)
        self._endif_def(symbol, ctx=ctx)

    def _open_extern_c(self, ctx: GenCtx):
        self._ifdef("__cplusplus", body="extern \"C\" {", ctx=ctx)

    def _close_extern_c(self, ctx: GenCtx):
        self._ifdef("__cplusplus", body="} // extern \"C\"", ctx=ctx)

    @staticmethod
    def _is_sys_header(hname: str) -> bool:
        return ("." not in hname) or hname.startswith("std")

    @staticmethod
    def _enclosed_hname(hname: str) -> str:
        return f"<{hname}>" if CppGenerator._is_sys_header(hname) else f"\"{hname}\""

    def _include(self, names, *, ctx: GenCtx):
        if isinstance(names, str):
            names = names.split("\n")
        ctx.add_lines([f"#include {CppGenerator._enclosed_hname(h)}" for h in names])

    def _pragma(self, pg: str, *, ctx: GenCtx):
        ctx.add_lines(f"#pragma {pg}")

    def _define(self, symbol: str, value: Optional[str], *, ctx: GenCtx):
        if value is not None:
            ctx.add_lines(f"#define {symbol} {value}")
        else:
            ctx.add_lines(f"#define {symbol}")

    def _open_ns(self, ns: str, *, ctx: GenCtx):
        ctx.add_lines(f"namespace {ns} {{")
        ctx.push_indent()

    def _close_ns(self, ns: str, *, ctx: GenCtx):
        ctx.pop_indent()
        ctx.add_lines(f"}} // namespace {ns}")

    def _api_ns(self, api: ApiDef):
        return api.name.replace("_", "::")

    def _generate_api(self, api: ApiDef, src_ctx: GenCtx, hdr_ctx: Optional[GenCtx]):
        ctx = hdr_ctx
        self._pragma("once", ctx=ctx)
        self._include("stdlib.h", ctx=ctx)
        api_ns = self._api_ns(api)
        self._open_ns(api_ns, ctx=ctx)
        # TODO: add interface class proto
        self._close_ns(api_ns, ctx=ctx)


class CBindingsGenerator(CppGenerator):
    # produces cpp file, use extern "C" internally
    _hdr_sfx = "_cbindings.h"
    _src_sfx = "_cbindings.cpp"

    def __init__(self):
        super().__init__()

    def _generate_api(self, api: ApiDef, src_ctx: GenCtx, hdr_ctx: Optional[GenCtx]):
        ctx = hdr_ctx
        self._pragma("once", ctx=ctx)
        self._include("stdlib.h", ctx=ctx)
        self._open_extern_c(ctx)
        # TODO: insert c wrapper types and protos
        self._close_extern_c(ctx)

        ctx = src_ctx
        self._include([self._header_name(api), CppGenerator()._header_name(api)], ctx=ctx)
        self._open_extern_c(ctx)
        # TODO: insert c wrapper impl
        self._close_extern_c(ctx)


class WasmBindingGenerator(CppGenerator):
    _hdr_sfx = None
    _src_sfx = "_wasm_bindings.cpp"

    def __init__(self, *, sfx: Optional[str] = None):
        super().__init__()

    def _generate_api(self, api: ApiDef, src_ctx: GenCtx, hdr_ctx: Optional[GenCtx]):
        ctx = src_ctx
        self._include("stdlib.h", ctx=ctx)


class JSGenerator(Generator):
    _src_sfx = ".js"

    def __init__(self):
        super().__init__()

    _comment = CppGenerator._comment

    def _generate_api(self, api: ApiDef, src_ctx: GenCtx, hdr_ctx: Optional[GenCtx]):
        src_ctx.add_lines(self._comment("JS"))


class JniBindingGenerator(CppGenerator):
    _hdr_sfx = None
    _src_sfx = "_jni_bindings.cpp"

    def __init__(self):
        super().__init__()

    def _generate_api(self, api: ApiDef, src_ctx: GenCtx, hdr_ctx: Optional[GenCtx]):
        ctx = src_ctx
        self._include(["jni.h", CppGenerator()._header_name(api)], ctx=ctx)
        self._open_extern_c(ctx)
        # TODO: jni binding impls
        self._close_extern_c(ctx)

class KtGenerator(Generator):
    _src_sfx = ".kt"

    def __init__(self):
        super().__init__()

    _comment = CppGenerator._comment

    def _generate_api(self, api: ApiDef, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        src_ctx.add_lines("import com.google.android.foo")


class SwiftBindingGenerator(CppGenerator):
    _src_sfx = "_swift_bindings.cpp"
    _hdr_sfx = "_.h"

    def __init__(self):
        super().__init__()

    def _generate_api(self, api: ApiDef, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        ctx = hdr_ctx
        self._pragma("once", ctx=ctx)
        self._open_extern_c(ctx)
        # TODO: swift binding protos
        self._close_extern_c(ctx)

        ctx = src_ctx
        self._include(["stdlib.h", CBindingsGenerator()._header_name(api)], ctx=ctx)
        self._open_extern_c(ctx)
        # TODO: swift binding impls
        self._close_extern_c(ctx)


class SwiftGenerator(Generator):
    _src_sfx = ".swift"

    def __init__(self):
        super().__init__()

    _comment = CppGenerator._comment

    def _generate_api(self, api: ApiDef, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        src_ctx.add_lines("import Foundation")


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

    CppGenerator().generate_api(api_def, cpp_dir)
    CBindingsGenerator().generate_api(api_def, c_dir)
    WasmBindingGenerator().generate_api(api_def, wasm_binding_dir)
    JSGenerator().generate_api(api_def, js_dir)
    JniBindingGenerator().generate_api(api_def, jni_binding_dir)
    KtGenerator().generate_api(api_def, kotlin_dir)
    SwiftBindingGenerator().generate_api(api_def, swift_binding_dir)
    SwiftGenerator().generate_api(api_def, swift_dir)

if __name__ == "__main__":
    app()
