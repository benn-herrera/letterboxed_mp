#!/usr/bin/env python3
import os
import sys
from datetime import datetime
from typing import Optional, Any

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

    def is_attr_optional(self, attr_name: str) -> bool:
        return False


class BaseType(Named):
    def __init__(self, name: Optional[str] = None):
        super().__init__(name)

    @property
    def type(self) -> str:
        return self.name

    @property
    def is_int(self) -> bool:
        return False

    @property
    def is_float(self) -> bool:
        return False

    @property
    def is_number(self) -> bool:
        return self.is_int or self.is_float

    @property
    def is_void(self) -> bool:
        return False

    @property
    def type_obj(self) -> 'BaseType':
        return self

    @property
    def resolved_type_obj(self) -> 'BaseType':
        return self

    def __str__(self):
        return f"{self.__class__.__name__} {self.name}"

_type_table = {}

def _add_type(typ: BaseType):
    if not isinstance(typ, BaseType):
        raise ValueError(f"{typ} is not a type.")
    if typ.name in _type_table:
        raise ValueError(f"{typ.name} already defined as {_type_table[typ.name]}, can't redefine as {typ}")
    _type_table[typ.name] = typ

def _get_type(name: str, *, is_void_legal: bool = False) -> BaseType:
    if name not in _type_table:
        raise ValueError(f"type {name} is not in the type table")
    t = _type_table[name]
    if (not is_void_legal) and (t.name == "void"):
        raise ValueError(f"{t} is not legal here.")
    return t


class PrimitiveType(BaseType):
    def __init__(self, name: str):
        super().__init__(name)

    @property
    def is_int(self) -> bool:
        return "int" in self.name

    @property
    def is_float(self) -> bool:
        return "float" in self.name

    @property
    def is_void(self) -> bool:
        return self.name == "void"


class TypedValue(Named):
    def __init__(self, *, is_void_legal: bool = False):
        super().__init__()
        self.type: Optional[str] = None
        self.is_reference = False
        self.array_count = None
        self.is_list = False
        self._is_void_legal = is_void_legal

    def is_attr_optional(self, attr_name: str) -> bool:
        if not attr_name in self.__dict__:
            raise ValueError(f"{attr_name} is not an attribute of {self}")
        return attr_name in ["is_reference", "is_list", "array_count"]

    def _validate(self):
        if self.is_list and self.is_array:
            raise ValueError(f"{self} - array_count and is_list are mutually exclusive")
        if self.resolved_type_obj.is_void and (self.is_list or self.is_array):
            raise ValueError(f"{self} - can't have list or array of void")

    @property
    def is_array(self):
        return self.array_count is not None

    @property
    def type_obj(self) -> BaseType:
        return _get_type(self.type, is_void_legal=self._is_void_legal)

    @property
    def resolved_type_obj(self) -> BaseType:
        return self.type_obj.resolved_type_obj

    @property
    def is_int(self) -> bool:
        return self.resolved_type_obj.is_int

    @property
    def is_float(self) -> bool:
        return self.resolved_type_obj.is_float

    @property
    def is_number(self) -> bool:
        return self.resolved_type_obj.is_number

    @property
    def is_void(self) -> bool:
        return self.resolved_type_obj.is_void

    def __str__(self):
        if self.is_array:
            mods = f"[{self.array_count}]"
        elif self.is_list:
            mods = "[list]"
        elif self.is_reference:
            mods = "(ref)"
        else:
            mods = ""
        return f"{self.__class__.__name__} {self.name}: {self.type_obj}{mods}"


class ConstantDef(TypedValue):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.value = None
        if dct:
            _init_obj_from_dict(self, dct)
            self._validate()

    def _validate(self):
        super()._validate()
        ct = self.resolved_type_obj
        if (self.is_reference or self.is_list or self.is_array) or not ct.is_number:
            raise ValueError(f"{self} type {ct} is not a simple numeric type.")


class EnumValue(TypedValue):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.value = None
        self.type = None
        if dct:
            # prevent griping about missing init member in dict
            _init_obj_from_dict(self, dct)
            self._validate()


class EnumDef(BaseType):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__(dct)
        self.members = []
        self.base_type = "int32"
        if dct:
            _init_obj_from_dict(self, dct)
            rbt = self.resolved_base_type_obj
            if not rbt.is_int:
                raise ValueError(f"{self} is not integral.")
            _add_type(self)
            self.members = [EnumValue(dict(**m, type=self.name)) for m in self.members]

    def __str__(self):
        return super().__str__() + f"({self.base_type})"

    @property
    def base_type_obj(self) -> BaseType:
        return _get_type(self.base_type, is_void_legal=False)

    @property
    def resolved_base_type_obj(self) -> BaseType:
        return self.base_type_obj.resolved_type_obj

    @property
    def is_int(self) -> bool:
        return True

    def is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["base_type"] or super().is_attr_optional(attr_name)


class AliasDef(BaseType):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.base_type = None
        self.is_reference = False
        if dct:
            _init_obj_from_dict(self, dct)
            _add_type(self)

    @property
    def base_type_obj(self) -> BaseType:
        return _get_type(self.base_type, is_void_legal=False)

    @property
    def resolved_type_obj(self):
        bt = self.base_type
        while isinstance(bt, AliasDef):
            bt = self.base_type_obj
        return bt

    @property
    def is_int(self) -> bool:
        return self.resolved_type_obj.is_int

    @property
    def is_float(self) -> bool:
        return self.resolved_type_obj.is_float

    @property
    def is_void(self) -> bool:
        return self.resolved_type_obj.is_void

    def is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["is_reference"] or super().is_attr_optional(attr_name)


class MemberDef(TypedValue):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        if dct:
            _init_obj_from_dict(self, dct)
            _ = self.type_obj
            self._validate()


class StructDef(BaseType):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.members = []
        if dct:
            _init_obj_from_dict(self, dct)
            _add_type(self)
            self.members = [MemberDef(m) for m in self.members]


class ParameterDef(TypedValue):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.is_list = False
        if dct:
            _init_obj_from_dict(self, dct)
            _ = self.type_obj
            if self.array_count is not None:
                raise ValueError(f"{self} - can't pass arrays as parameters")
            self._validate()


class MethodDef(TypedValue):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__(is_void_legal=True)
        self.parameters = []
        self.is_static = False
        self.is_const = False
        if dct:
            _init_obj_from_dict(self, dct)
            _ = self.type_obj
            self.parameters = [ParameterDef(p) for p in self.parameters]
            self._validate()
            if self.array_count is not None:
                raise ValueError(f"{self} - can't return an array")

    def is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["is_static", "is_const"] or super().is_attr_optional(attr_name)


class ClassDef(BaseType):
    def __init__(self, dct: Optional[dict] = None):
        super().__init__()
        self.members = []
        self.methods = []
        if dct:
            _init_obj_from_dict(self, dct)
            _add_type(self)
            self.members = [MemberDef(m) for m in self.members]
            self.methods = [MethodDef(m) for m in self.methods]


class FunctionDef(TypedValue):
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

class BlockCtx:
    def __init__(
            self,
            push_lines: Optional[str],
            *,
            indent: bool = False,
            pre_pop_lines: Optional[Any] = None,
            post_pop_lines: Optional[Any] = None,
            on_pre_pop: Optional[callable] = None,
            on_post_pop: Optional[callable] = None):
        self.push_lines = push_lines
        self.indent = indent
        self.on_pre_pop = on_pre_pop
        self.on_post_pop = on_post_pop
        self.pre_pop_lines = pre_pop_lines
        self.post_pop_lines = post_pop_lines
        self.block_indent = None

class GenCtx:
    def __init__(self, api: ApiDef, *, out_dir: Path):
        self._indent_count = 0
        self._block_ctx_stack: [BlockCtx] = []
        self._lines = []
        self._api = api
        self._out_dir = out_dir

    @property
    def api(self) -> ApiDef:
        return self._api

    @property
    def out_dir(self) -> Path:
        return self._out_dir

    @property
    def indentation(self) -> str:
        return "  " * self._indent_count if self._indent_count > 0 else ""

    def push_indent(self) -> int:
        self._indent_count += 1
        return self._indent_count

    def pop_indent(self, *, expected_cur_indent: Optional[int] = None):
        if self._indent_count == 0:
            raise Exception("can't reduce indent below 0")
        if expected_cur_indent is not None and expected_cur_indent != self._indent_count:
            raise Exception(f"expected current indent {expected_cur_indent} but it is {self._indent_count}")
        self._indent_count -= 1

    def push_block(
            self,
            push_lines: Optional[str],
            *,
            indent: bool = False,
            pre_pop_lines: Optional[Any] = None,
            post_pop_lines: Optional[Any] = None,
            on_pre_pop: Optional[callable] = None,
            on_post_pop: Optional[callable] = None
    ) -> BlockCtx:
        # not using *args and **kwargs for IDE code completion mercy
        block = BlockCtx(
            push_lines,
            indent=indent,
            pre_pop_lines=pre_pop_lines,
            post_pop_lines=post_pop_lines,
            on_pre_pop=on_pre_pop,
            on_post_pop=on_post_pop
        )
        if block.push_lines is not None:
            self.add_lines(block.push_lines)
        if block.indent:
            block.block_indent = self.push_indent()
        self._block_ctx_stack.append(block)
        return self._block_ctx_stack[-1]

    def pop_block(self, expected_block: Optional[BlockCtx] = None):
        if not self._block_ctx_stack:
            raise Exception("ctx stack is empty")
        block = self._block_ctx_stack.pop(-1)
        if expected_block is not None and expected_block is not block:
            raise ValueError("closing unexpected context")
        if callable(block.on_pre_pop):
            block.on_pre_pop()
        if block.pre_pop_lines is not None:
            self.add_lines(block.pre_pop_lines)
        if block.indent:
            self.pop_indent(expected_cur_indent=block.block_indent)
        if block.post_pop_lines is not None:
            self.add_lines(block.post_pop_lines)
        if callable(block.on_post_pop):
            block.on_post_pop()

    def add_lines(self, lines):
        if isinstance(lines, str):
            lines = lines.split('\n')
        elif isinstance(lines, list) and isinstance(lines[0], str):
            pass
        else:
            raise ValueError(f"{lines} is not a string or string list")
        self._lines.extend([f"{self.indentation}{ln}" for ln in lines])

    @property
    def line_count(self) -> int:
        return len(self._lines)

    @property
    def ctx(self):
        if not self._block_ctx_stack:
            raise Exception("ctx stack is empty")
        return self._block_ctx_stack[-1]

    def get_gen_text(self) -> str:
        if self._block_ctx_stack or self._indent_count > 0:
            raise Exception("indent and/or context stack have more pushes than pops")
        return "\n".join(self._lines) + "\n"


class Generator:
    _hdr_sfx = None
    _src_sfx = None

    def __init__(self, timestamp: Optional[str] = None):
        self.timestamp = timestamp

    @property
    def name(self):
        return self.__class__.__name__

    def _header_name(self, api: ApiDef) -> Optional[str]:
        return f"{api.name}{self._hdr_sfx}" if self._hdr_sfx else None

    def _src_name(self, api: ApiDef) -> Optional[str]:
        return f"{api.name}{self._src_sfx}" if self._src_sfx else None

    def _comment(self, text: str) -> [str]:
        raise Exception(f"_comment not implemented in {self.name}")

    def _generate_api(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        raise Exception(f"_generate_api not implemented in {self.name}")

    def generate_api(self, api: ApiDef, out_dir: Path):
        src_out_path = None
        src_ctx = None
        hdr_out_path = None
        hdr_ctx = None

        os.makedirs(out_dir.as_posix(), exist_ok=True)

        if self._hdr_sfx:
            hdr_ctx = GenCtx(api, out_dir=out_dir)
            hdr_out_path = out_dir / self._header_name(api)
            hdr_ctx.add_lines(self._comment(f"{hdr_out_path.name} v{api.version} generated by {SCRIPT_NAME} {self.timestamp}"))

        if self._src_sfx:
            src_ctx = GenCtx(api, out_dir=out_dir)
            src_out_path = out_dir / self._src_name(api)
            src_ctx.add_lines(self._comment(f"{src_out_path.name} v{api.version} generated by {SCRIPT_NAME} {self.timestamp}"))

        if not (src_ctx or hdr_ctx):
            raise Exception(f"{self.name} does not not have valid _src_sfx or _hdr_sfx")

        self._generate_api(src_ctx=src_ctx, hdr_ctx=hdr_ctx)

        if hdr_ctx and (hdr_ctx.line_count > 1):
            hdr_out_path.write_text(hdr_ctx.get_gen_text(), encoding="utf-8", newline="\n")

        if src_ctx and (src_ctx.line_count > 1):
            src_out_path.write_text(src_ctx.get_gen_text(), encoding="utf-8", newline="\n")


class CppGenerator(Generator):
    _hdr_sfx = ".h"
    _use_std = False

    def __init__(self, timestamp: Optional[str] = None):
        super().__init__(timestamp)

    def _comment(self, text: str) -> [str]:
        return [f"// {ln}" for ln in text.split("\n")]

    def _push_ifdef_block(self, symbol: str, *, ctx: GenCtx) -> BlockCtx:
        return ctx.push_block(f"#if defined({symbol})", post_pop_lines=f"#endif // defined({symbol})")

    def _push_extern_c_block(self, ctx: GenCtx) -> BlockCtx:
        def on_post_pop():
            block = self._push_ifdef_block("__cplusplus", ctx=ctx)
            ctx.add_lines("} // extern \"C\"")
            ctx.pop_block(block)

        ec_block = ctx.push_block(None, on_pre_pop=on_post_pop)

        ifdef_block = self._push_ifdef_block("__cplusplus", ctx=ctx)
        ctx.add_lines("extern \"C\" {")
        ctx.pop_block(ifdef_block)
        return ec_block

    @staticmethod
    def _is_sys_header(hname: str) -> bool:
        return ("." not in hname) or hname.startswith("std")

    @staticmethod
    def _enclosed_hname(hname: str) -> str:
        if "\"" in hname or "<" in hname:
            return hname
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

    def _api_ns(self, api: ApiDef):
        return api.name.replace("_", "::")

    def _gen_primitive_typename(self, prim_type: PrimitiveType, *, api: ApiDef, is_formal: bool = False) -> str:
        _ = api
        if prim_type.name in ["void", "bool"]:
            return prim_type.name
        if prim_type.is_int:
            return f"{prim_type.name}_t"
        if prim_type.is_float:
            return "double" if prim_type.name.endswith("64") else "float"
        if self._use_std:
            if "string" in prim_type.name:
                return "const std::string&" if is_formal else "std::string"
        else:
            if prim_type.name == "string":
                return "const char*" if is_formal else "char*"
            if prim_type.name == "const_string":
                return "const char*"

        return f"const {prim_type.name}&" if is_formal else prim_type.name

    def _gen_typename(self, type_obj, *, api: ApiDef, is_formal: bool = False) -> str:
        if isinstance(type_obj, PrimitiveType):
            return self._gen_primitive_typename(type_obj, api=api, is_formal=is_formal)
        return f"const {type_obj.name}&" if is_formal else type_obj.name

    def _gen_alias(self, alias_def: AliasDef, *, ctx: GenCtx):
        ref = "*" if alias_def.is_reference else ""
        ctx.add_lines(f"using {alias_def.name} = {self._gen_typename(alias_def.type_obj, api=ctx.api)}{ref};")

    def _gen_const(self, const_def: ConstantDef, *, ctx: GenCtx):
        cval = const_def.value
        type_obj = const_def.resolved_type_obj
        if "." in f"{cval}" and "32" in type_obj.name:
            cval = f"{cval}f"
        ctx.add_lines(f"static constexpr {self._gen_typename(const_def.type_obj, api=ctx.api)} {const_def.name} = {cval};")

    def _gen_enum_value(self, eval_def: EnumValue, *, ctx: GenCtx, sep: str):
        ctx.add_lines(f"{eval_def.name} = {eval_def.value}{sep}")

    def _gen_enum(self, enum_def: EnumDef, *, ctx: GenCtx, is_forward: bool = False):
        base_type = ""
        if not enum_def.type_obj.is_void:
            base_type = f" : {self._gen_typename(enum_def.type_obj, api=ctx.api)}"
        term = ";" if is_forward else " {"
        enum_block = ctx.push_block(
            f"enum class {enum_def.name}{base_type}{term}",
            indent=True,
            post_pop_lines="};\n" if not is_forward else None
        )
        if not is_forward:
            for (i, eval_def) in enumerate(enum_def.members):
                self._gen_enum_value(
                    eval_def,
                    ctx=ctx,
                    sep=("," if i != len(enum_def.members) - 1 else ""))
        ctx.pop_block(enum_block)

    def _gen_member(self, member_def: MemberDef, *, ctx: GenCtx):
        if member_def.is_list:
            if self._use_std:
                ctx.add_lines(f"std::vector<{self._gen_typename(member_def.type_obj, api=ctx.api)}> {member_def.name};")
            else:
                ctx.add_lines([
                    f"{self._gen_typename(member_def.type_obj, api=ctx.api)} {member_def.name};",
                    f"{self._gen_typename(_get_type('int32'), api=ctx.api)} {member_def.name}_count;",
                ])
        else:
            array_count = member_def.array_count
            if self._use_std and array_count is not None:
                ctx.add_lines(f"std::array<{self._gen_typename(member_def.type_obj, api=ctx.api)}, {array_count}> {member_def.name};")
            else:
                array_size = "" if array_count is None else f"[{array_count}]"
                ctx.add_lines(f"{self._gen_typename(member_def.type_obj, api=ctx.api)} {member_def.name}{array_size};")

    def _gen_struct(self, struct_def: StructDef, *, ctx: GenCtx, is_forward: bool = False):
        term = ";" if is_forward else " {"
        struct_decl = f"struct {struct_def.name}{term}"
        struct_block = ctx.push_block(
            struct_decl,
            indent=True,
            post_pop_lines=("};\n" if not is_forward else None)
        )
        if not is_forward:
            for member_def in struct_def.members:
                self._gen_member(member_def, ctx=ctx)
        ctx.pop_block(struct_block)

    def _gen_param(self, param_def: ParameterDef, *, ctx: GenCtx, sep: str) -> str:
        if param_def.is_list:
            type_str = self._gen_typename(param_def.type_obj, api=ctx.api)
            if self._use_std:
                return f"const std::vector<{type_str}>& {param_def.name}{sep}"
            return f"const {type_str}* {param_def.name}, {_get_type('int32')} {param_def.name}_count{sep}"
        return f"{self._gen_typename(param_def.type_obj, api=ctx.api, is_formal=True)} {param_def.name}{sep}"

    def _gen_method(self, method_def: MethodDef, *, ctx: GenCtx, is_forward: bool = False, is_abstract: bool = False):
        if method_def.is_const and method_def.is_static:
            raise ValueError(f"{method_def} can't be both static and const.")
        ref = "*" if method_def.is_reference else ""
        line = [
            "static " if method_def.is_static else "",
            f"{self._gen_typename(method_def.type_obj, api=ctx.api)}{ref} {method_def.name}("
        ]
        for (i, param_def) in enumerate(method_def.parameters):
            line.append(
                self._gen_param(
                    param_def,
                    ctx=ctx,
                    sep=(", " if i != len(method_def.parameters) - 1 else "")))
        line.append(")")
        if method_def.is_const:
            line.append(" const")
        if is_abstract and not method_def.is_static:
            line.append(" = 0;")
        elif is_forward:
            line.append(";")
        else:
            raise Exception(f"{method_def}: method body generation not supported.")
        ctx.add_lines("".join(line))

    def _gen_class(self, class_def: ClassDef, *, ctx: GenCtx, is_forward: bool = False, is_abstract: bool = False):
        term = ";" if is_forward else " {"
        class_decl = f"class {class_def.name}{term}"
        class_block = ctx.push_block(
            class_decl,
            post_pop_lines="};\n" if not is_forward else None
        )

        if not is_forward:
            protected_block = ctx.push_block("protected:", indent=True, post_pop_lines="")
            ctx.add_lines(f"{class_def.name}() = default;")
            ctx.pop_block(protected_block)

            public_block = ctx.push_block("public:", indent=True)
            ctx.add_lines(f"virtual ~{class_def.name}() = default;")
            for method_def in class_def.methods:
                self._gen_method(method_def, ctx=ctx, is_forward=True, is_abstract=is_abstract)

            for member_def in class_def.members:
                self._gen_member(member_def, ctx=ctx)
            ctx.pop_block(public_block)

        ctx.pop_block(class_block)

    def _gen_function(self, func_def: FunctionDef, *, ctx: GenCtx, is_forward: bool = False):
        ref = "*" if func_def.is_reference else ""
        line = [
            f"{self._gen_typename(func_def.type_obj, api=ctx.api)}{ref} {func_def.name}("
        ]
        for (i, param_def) in enumerate(func_def.parameters):
            line.append(
                self._gen_param(
                    param_def,
                    ctx=ctx,
                    sep=(", " if i != len(func_def.parameters) - 1 else "")))
        if is_forward:
            line.append(");")
        else:
            raise Exception(f"{func_def}: function body generation not supported.")
        ctx.add_lines("".join(line))

    def _generate_api(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        ctx = hdr_ctx
        api = ctx.api
        self._pragma("once", ctx=ctx)
        self._include("stdlib.h", ctx=ctx)
        if self._use_std:
            self._include(["vector", "string"], ctx=ctx)
        api_ns = self._api_ns(api)

        ns_block = ctx.push_block(
            f"\nnamespace {api_ns} {{",
            indent=True,
            post_pop_lines=f"}} // namespace {api_ns}"
        )

        if api.aliases:
            for alias_def in api.aliases:
                self._gen_alias(alias_def, ctx=ctx)
            ctx.add_lines("")

        if api.constants:
            for const_def in api.constants:
                self._gen_const(const_def, ctx=ctx)
            ctx.add_lines("")

        for enum_def in api.enums:
            self._gen_enum(enum_def, ctx=ctx)

        for struct_def in api.structs:
            self._gen_struct(struct_def, ctx=ctx)

        for class_def in api.classes:
            self._gen_class(class_def, ctx=ctx, is_abstract=True)

        for function_def in api.functions:
            self._gen_function(function_def, ctx=ctx, is_forward=True)

        ctx.pop_block(ns_block)


class CBindingsGenerator(CppGenerator):
    _hdr_sfx = "_cbindings.h"
    _src_sfx = "_cbindings.cpp"
    _use_std = False

    def __init__(self, timestamp: Optional[str] = None):
        super().__init__(timestamp)

    def _gen_primitive_typename(self, prim_type: PrimitiveType, *, api: ApiDef, is_formal: bool = False) -> str:
        _ = api
        if prim_type.name == "bool":
            return prim_type.name
        if prim_type.is_int:
            return f"{prim_type.name}_t"
        if prim_type.is_float:
            return "double" if prim_type.name.endswith("64") else "float"
        if prim_type.name == "string":
            return "const char*" if is_formal else "char*"
        if prim_type.name == "const_string":
            return "const char*"
        return f"const {prim_type.name}*" if is_formal else prim_type.name

    def _gen_alias(self, alias_def: AliasDef, *, ctx: GenCtx):
        ref = "*" if alias_def.is_reference else ""
        ctx.add_lines(f"typedef {self._gen_typename(alias_def.type_obj, api=ctx.api)}{ref} {alias_def.name};")

    def _gen_enum(self, enum_def: EnumDef, *, ctx: GenCtx, is_forward: bool = False):
        enum_decl = f"enum {enum_def.name}"
        term = ";" if is_forward else " {"
        ctx.add_lines(f""
                      f"{enum_decl}{term}")
        if is_forward:
            return
        if enum_def.members:
            enum_block = ctx.push_block(
                enum_decl,
                indent=True,
                post_pop_lines="};"
            )
            for (i, eval_def) in enumerate(enum_def.members):
                self._gen_enum_value(
                    eval_def,
                    ctx=ctx,
                    sep=("," if i != len(enum_def.members) - 1 else ""))
            ctx.pop_block(enum_block)

    def _gen_struct(self, struct_def: StructDef, *, ctx: GenCtx, is_forward: bool = False):
        super()._gen_struct(struct_def, ctx=ctx, is_forward=is_forward)
        ctx.add_lines(f"typedef struct {struct_def.name} {struct_def.name};")

    def _generate_api(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        ctx = hdr_ctx
        self._pragma("once", ctx=ctx)
        self._include("stdlib.h", ctx=ctx)
        ec_block = self._push_extern_c_block(ctx)
        # TODO: insert c wrapper types and protos
        ctx.pop_block(ec_block)

        ctx = src_ctx
        api = ctx.api
        self._include([self._header_name(api), CppGenerator()._header_name(api)], ctx=ctx)
        ec_block = self._push_extern_c_block(ctx)
        # TODO: insert c wrapper types and protos
        ctx.pop_block(ec_block)


class WasmBindingGenerator(CppGenerator):
    _hdr_sfx = None
    _src_sfx = "_wasm_bindings.cpp"
    _use_std = True

    def __init__(self, timestamp: Optional[str] = None):
        super().__init__(timestamp)

    def _generate_api(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        ctx = src_ctx
        self._include("stdlib.h", ctx=ctx)


class JSGenerator(Generator):
    _src_sfx = ".js"

    def __init__(self, timestamp: Optional[str] = None):
        super().__init__(timestamp)

    _comment = CppGenerator._comment

    def _generate_api(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        src_ctx.add_lines(self._comment("JS"))


class JniBindingGenerator(CppGenerator):
    _hdr_sfx = None
    _src_sfx = "_jni_bindings.cpp"

    def __init__(self, timestamp: Optional[str] = None):
        super().__init__(timestamp)

    def _generate_api(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        ctx = src_ctx
        api = ctx.api
        self._include(["jni.h", CppGenerator()._header_name(api)], ctx=ctx)
        ec_block = self._push_extern_c_block(ctx)
        # TODO: jni binding impls
        ctx.pop_block(ec_block)

class KtGenerator(Generator):
    _src_sfx = ".kt"

    def __init__(self, timestamp: Optional[str] = None):
        super().__init__(timestamp)

    _comment = CppGenerator._comment

    def _generate_api(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        src_ctx.add_lines("import com.google.android.foo")


class SwiftBindingGenerator(CppGenerator):
    _src_sfx = "_swift_bindings.cpp"
    _hdr_sfx = "_.h"

    def __init__(self, timestamp: Optional[str] = None):
        super().__init__(timestamp)

    def _generate_api(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        ctx = hdr_ctx
        api = ctx.api
        self._pragma("once", ctx=ctx)

        ec_block = self._push_extern_c_block(ctx)
        # TODO: swift binding protos
        ctx.pop_block(ec_block)

        ctx = src_ctx
        self._include(["stdlib.h", CBindingsGenerator()._header_name(api)], ctx=ctx)
        ec_block = self._push_extern_c_block(ctx)
        # TODO: swift binding impls
        ctx.pop_block(ec_block)


class SwiftGenerator(Generator):
    _src_sfx = ".swift"

    def __init__(self, timestamp: Optional[str] = None):
        super().__init__(timestamp)

    _comment = CppGenerator._comment

    def _generate_api(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        src_ctx.add_lines("import Foundation")


def _init_type_table():
    global _type_table
    _type_table = {}
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
        _add_type(PrimitiveType(base_type))


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

    timestamp = f"{datetime.now()}"

    CppGenerator(timestamp).generate_api(api_def, cpp_dir)
    CBindingsGenerator(timestamp).generate_api(api_def, c_dir)
    WasmBindingGenerator(timestamp).generate_api(api_def, wasm_binding_dir)
    JSGenerator(timestamp).generate_api(api_def, js_dir)
    JniBindingGenerator(timestamp).generate_api(api_def, jni_binding_dir)
    KtGenerator(timestamp).generate_api(api_def, kotlin_dir)
    SwiftBindingGenerator(timestamp).generate_api(api_def, swift_binding_dir)
    SwiftGenerator(timestamp).generate_api(api_def, swift_dir)

if __name__ == "__main__":
    app()
