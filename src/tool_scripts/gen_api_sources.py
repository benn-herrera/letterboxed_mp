#!/usr/bin/env python3
import os
from datetime import datetime
from typing import Optional, Any, Tuple, Set

import cyclopts
import json
from pathlib import Path

gen_api_version = "0.5.0"

app = cyclopts.App(
    version=gen_api_version,
    name=Path(__file__).name
)

def snake_to_camel(val: str, *, capitalize=False) -> str:
    return ''.join([(s.capitalize() if (capitalize or i > 0) else s) for (i, s) in enumerate(val.split('_'))])

class Base:
    def __init__(self, **kwargs):
        dct_keys = set(kwargs.keys())
        unset_attrs = set()
        for field in [field for (field, value) in self.__dict__.items() if
                      Base._is_public_data_member(self, field, value)]:
            if field in kwargs:
                setattr(self, field, kwargs.get(field))
                dct_keys.remove(field)
            else:
                if self._is_attr_optional(field):
                    continue
                unset_attrs.add(field)
        err_msgs = []
        if dct_keys:
            err_msgs.append(f"{dct_keys} are not attributes of {self.__class__.__name__} {getattr(self, 'name', '')}")
        if unset_attrs:
            err_msgs.append(
                f"{unset_attrs} are required attributes of {self.__class__.__name__} {getattr(self, 'name', '')} but were not set")
        if err_msgs:
            raise ValueError("\n".join(err_msgs))
        self._validate()

    def _is_attr_optional(self, attr_name: str) -> bool:
        return False

    def _validate(self):
        pass

    @staticmethod
    def _is_public_data_member(obj, field: str, value) -> bool:
        return (not field.startswith("_")) and (not callable(value))


class Named(Base):
    def __init__(self, **kwargs):
        self.name: Optional[str] = None
        super().__init__(**kwargs)

    def __str__(self):
        return f"{self.name}{{{self.__class__.__name__}}}"


class BaseType(Named):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        _add_type(self)

    def __str__(self):
        return f"{self.__class__.__name__} {self.name}"

    # @property
    # def type(self) -> str:
    #     return self.name

    @property
    def is_int(self) -> bool:
        return False

    @property
    def is_bool(self) -> bool:
        return False

    @property
    def is_float(self) -> bool:
        return False

    @property
    def is_primitive(self) -> bool:
        return False

    @property
    def is_number(self) -> bool:
        return self.is_int or self.is_float

    @property
    def is_number_or_bool(self) -> bool:
        return self.is_number or self.is_bool

    @property
    def is_void(self) -> bool:
        return False

    @property
    def is_string(self) -> bool:
        return False

    @property
    def type_obj(self) -> 'BaseType':
        return self

    @property
    def resolved_type_obj(self) -> 'BaseType':
        return self


class PrimitiveType(BaseType):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def is_int(self) -> bool:
        return "int" in self.name

    @property
    def is_float(self) -> bool:
        return "float" in self.name

    @property
    def is_void(self) -> bool:
        return self.name == "void"

    @property
    def is_string(self) -> bool:
        return self.name == "string"

    @property
    def is_bool(self) -> bool:
        return self.name == "bool"

    @property
    def is_primitive(self) -> bool:
        return True


class TypedNamed(Named):
    def __init__(self, **kwargs):
        self.type: Optional[str] = None
        self.is_reference = False
        self.array_count = None
        self.is_list = False
        self.is_const = False
        super().__init__(**kwargs)

    def _is_attr_optional(self, attr_name: str) -> bool:
        if not attr_name in self.__dict__:
            raise ValueError(f"{attr_name} is not an attribute of {self}")
        return attr_name in ["is_reference", "is_list", "is_const", "array_count"] or super()._is_attr_optional(attr_name)

    def _validate(self):
        if self.is_list and self.is_array:
            raise ValueError(f"{self} - array_count and is_list are mutually exclusive")
        if self.resolved_type_obj.is_void and (self.is_list or self.is_array or self.is_const):
            raise ValueError(f"{self} - void type can't be const, array, or list")

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

    @property
    def is_array(self):
        return self.array_count is not None

    @property
    def type_obj(self) -> BaseType:
        return get_type(self.type)

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
    def is_primitive(self) -> bool:
        return self.resolved_type_obj.is_primitive

    @property
    def is_number_or_bool(self) -> bool:
        return self.resolved_type_obj.is_number_or_bool

    @property
    def is_void(self) -> bool:
        return self.resolved_type_obj.is_void

    @property
    def is_string(self) -> bool:
        return self.resolved_type_obj.is_string

    @property
    def is_bool(self) -> bool:
        return self.resolved_type_obj.is_bool


class ConstantDef(TypedNamed):
    def __init__(self, **kwargs):
        self.value = None
        super().__init__(**kwargs)

    def _validate(self):
        super()._validate()
        if (self.is_reference or self.is_list or self.is_array) or not self.is_number:
            raise ValueError(f"{self} type {self} is not a simple numeric type.")
        if self.is_int and self.has_float_value:
            raise ValueError(f"{self} assigns a float value to an int type")

    def __str__(self):
        return f"{super().__str__()} = {self.value}"

    @property
    def has_float_value(self) -> bool:
        return "." in f"{self.value}"


class EnumValue(ConstantDef):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class EnumDef(BaseType):
    def __init__(self, **kwargs):
        self.members = []
        self.base_type = "int32"
        super().__init__(**kwargs)
        self.members = [EnumValue(**m, type=self.name) for m in self.members]

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["base_type"] or super()._is_attr_optional(attr_name)

    def _validate(self):
        super()._validate()
        rbt = self.resolved_base_type_obj
        if not rbt.is_int:
            raise ValueError(f"{self} is not integral.")

    def __str__(self):
        return super().__str__() + f"({self.base_type})"

    @property
    def base_type_obj(self) -> BaseType:
        return get_type(self.base_type)

    @property
    def resolved_base_type_obj(self) -> BaseType:
        return self.base_type_obj.resolved_type_obj

    @property
    def is_int(self) -> bool:
        return True


class AliasDef(BaseType):
    def __init__(self, **kwargs):
        self.base_type = None
        self.is_reference = False
        super().__init__(**kwargs)

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["is_reference"] or super()._is_attr_optional(attr_name)

    def _validate(self):
        super()._validate()
        if self.resolved_type_obj.is_void:
            raise ValueError(f"{self} - can't alias void type")

    @property
    def base_type_obj(self) -> BaseType:
        return get_type(self.base_type)

    @property
    def resolved_type_obj(self):
        bt = self.base_type_obj
        while isinstance(bt, AliasDef):
            bt = self.base_type_obj
        return bt


class MemberDef(TypedNamed):
    def __init__(self, **kwargs):
        self.is_static = False
        super().__init__(**kwargs)

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["is_static"] or super()._is_attr_optional(attr_name)

    def _validate(self):
        super()._validate()
        if self.resolved_type_obj.is_void:
            raise ValueError(f"{self} can't have a void type")


class StructDef(BaseType):
    def __init__(self, **kwargs):
        self.members = []
        super().__init__(**kwargs)
        self.members = [MemberDef(**m) for m in self.members]


class ParameterDef(TypedNamed):
    def __init__(self, **kwargs):
        self.is_list = False
        super().__init__(**kwargs)

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["is_list"] or super()._is_attr_optional(attr_name)

    def _validate(self):
        super()._validate()
        if self.is_array:
            raise ValueError(f"{self} - can't pass arrays as parameters")


class MethodDef(TypedNamed):
    def __init__(self, **kwargs):
        self.parameters = []
        self.is_static = False
        self.is_const = False
        super().__init__(**kwargs)
        self.parameters = [ParameterDef(**p) for p in self.parameters]

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["parameters", "is_static", "is_const"] or super()._is_attr_optional(attr_name)


class ClassDef(BaseType):
    def __init__(self, **kwargs):
        self.constants = []
        self.members = []
        self.methods = []
        super().__init__(**kwargs)
        self.constants = [ConstantDef(**c) for c in self.constants]
        self.members = [MemberDef(**m) for m in self.members]
        self.methods = [MethodDef(**m) for m in self.methods]

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["constants", "methods", "members"] or super()._is_attr_optional(attr_name)


class FunctionDef(TypedNamed):
    def __init__(self, **kwargs):
        self.parameters = []
        super().__init__(**kwargs)
        self.parameters = [ParameterDef(**p) for p in self.parameters]

    def _is_attr_optional(self, attr_name: str) -> bool:
        return attr_name in ["parameters"] or super()._is_attr_optional(attr_name)

class ApiDef(Named):
    def __init__(self, **kwargs):
        self.version: Optional[str] = None
        self.aliases = []
        self.classes = []
        self.constants = []
        self.enums = []
        self.functions = []
        self.structs = []
        super().__init__(**kwargs)

        init_type_table()
        self.constants = [ConstantDef(**c) for c in self.constants]
        self.enums = [EnumDef(**e) for e in self.enums]
        self.aliases = [AliasDef(**o) for o in self.aliases]
        self.structs = [StructDef(**s) for s in self.structs]
        self.classes = [ClassDef(**s) for s in self.classes]
        self.functions = [FunctionDef(**f) for f in self.functions]
        self.types_used_in_list = self._collate_types_used_in_list()

    def _is_attr_optional(self, attr_name: str) -> bool:
        return (attr_name in ["aliases", "classes", "constants", "enums", "functions", "structs"] or
                super()._is_attr_optional(attr_name))

    def _validate(self):
        if not (self.constants or self.enums or self.aliases or self.structs or self.classes or self.functions):
            raise ValueError(f"{self} defines no api")

    def _collate_types_used_in_list(self) -> Set[BaseType]:
        used_in_list = set()
        def register_list_usage(usage):
            if usage.is_list:
                used_in_list.add(usage.resolved_type_obj)
        def register_list_usages(usages):
            for usage in usages:
                register_list_usage(usage)
        register_list_usages(self.constants)

        for sd in self.structs:
            register_list_usages(sd.members)
        for cd in self.classes:
            register_list_usages(cd.members)
            register_list_usages(cd.methods)
            for md in cd.methods:
                register_list_usages(md.parameters)
        for fd in self.functions:
            register_list_usages(fd.parameters)
        return used_in_list


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
    def __init__(self, out_path: Path):
        self._indent_count = 0
        self._block_ctx_stack: [BlockCtx] = []
        self._lines = []
        self.out_path = out_path

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
    def lines(self) -> [str]:
        return list(self._lines)

    def get_gen_text(self) -> str:
        if self._block_ctx_stack or self._indent_count > 0:
            raise Exception("indent and/or context stack have more pushes than pops")
        return "\n".join(self._lines) + "\n"


class Generator:
    def __init__(self, api: ApiDef):
        self.api = api

    @property
    def name(self):
        return self.__class__.__name__

    def _comment(self, text: str) -> [str]:
        raise Exception(f"_comment not implemented in {self.name}")

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        raise Exception(f"_generate_api not implemented in {self.name}")

    def _add_comment(self, text: str, ctx: GenCtx):
        ctx.add_lines(self._comment(text))

    def generate_ctx(self, *, hdr: Optional[Path]=None, src: Optional[Path]=None) -> Tuple[Optional[GenCtx], Optional[GenCtx]]:
        def make_ctx(out_path: Optional[Path]) -> Optional[GenCtx]:
            if ctx := (GenCtx(out_path) if out_path else None):
                self._add_comment(
                    f"{ctx.out_path.name} v{self.api.version} generated by {Path(__file__).name} {datetime.now()}",
                    ctx=ctx
                )
            return ctx

        hdr_ctx = make_ctx(hdr)
        src_ctx = make_ctx(src)

        if not (src_ctx or hdr_ctx):
            raise Exception(f"{self.name} invoked with no output specified.")

        self._generate(hdr_ctx=hdr_ctx, src_ctx=src_ctx)

        return hdr_ctx, src_ctx

    def generate_files(self, *, hdr: Optional[Path] = None, src: Optional[Path] = None):
        for ctx in self.generate_ctx(hdr=hdr, src=src):
            if ctx and (ctx.line_count > 1):
                os.makedirs(ctx.out_path.parent.as_posix(), exist_ok=True)
                ctx.out_path.write_text(ctx.get_gen_text(), encoding="utf-8", newline="\n")


class CppGenerator(Generator):
    def __init__(self, api: ApiDef, *, use_std: bool=True):
        super().__init__(api)
        self.use_std = use_std

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        if src_ctx or not hdr_ctx:
            raise ValueError(f"{self.name} requires hdr_ctx, does not support src_ctx")
        ctx = hdr_ctx
        self._pragma("once", ctx=ctx)
        if self.use_std:
            self._include(["array", "string", "vector"], ctx=ctx)
        else:
            self._include("stdint.h", ctx=ctx)
        self._include("api/api_util.h", ctx=ctx)

        ns_block = ctx.push_block(
            f"\nnamespace {self.api_ns} {{",
            indent=True,
            post_pop_lines=f"}} // namespace {self.api_ns}"
        )

        if self.api.aliases:
            for alias_def in self.api.aliases:
                self._gen_alias(alias_def, ctx=ctx)
            ctx.add_lines("")

        if self.api.constants:
            for const_def in self.api.constants:
                self._gen_const(const_def, ctx=ctx)
            ctx.add_lines("")

        for enum_def in self.api.enums:
            self._gen_enum(enum_def, ctx=ctx)

        for struct_def in self.api.structs:
            self._gen_struct(struct_def, ctx=ctx)

        # id_block = self._push_ifdef_block("__cplusplus", ctx=ctx)
        for class_def in self.api.classes:
            self._gen_class(class_def, ctx=ctx, is_abstract=True)
        # ctx.pop_block(id_block)
        # del id_block

        for function_def in self.api.functions:
            self._gen_function(function_def, ctx=ctx, is_forward=True)

        if ns_block:
            ctx.pop_block(ns_block)

    def _comment(self, text: str) -> [str]:
        return [f"// {ln}" for ln in text.split("\n")]

    def _push_ifdef_block(self, symbol: str, *, ctx: GenCtx) -> BlockCtx:
        return ctx.push_block(f"#if defined({symbol})", post_pop_lines=f"#endif // defined({symbol})")

    def _push_extern_c_block(self, ctx: GenCtx) -> BlockCtx:
        def on_post_pop():
            ctx.add_lines("")
            block = self._push_ifdef_block("__cplusplus", ctx=ctx)
            ctx.add_lines("} // extern \"C\"")
            ctx.pop_block(block)

        ec_block = ctx.push_block(None, on_pre_pop=on_post_pop)

        ifdef_block = self._push_ifdef_block("__cplusplus", ctx=ctx)
        ctx.add_lines("extern \"C\" {")
        ctx.pop_block(ifdef_block)
        ctx.add_lines("")
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

    @property
    def api_ns(self):
        return self.api.name.replace("_", "::")

    def _gen_primitive_typename(self, prim_type: PrimitiveType) -> str:
        if prim_type.name in ["void", "bool"]:
            return prim_type.name
        if prim_type.is_int:
            return f"{prim_type.name}_t"
        if prim_type.is_float:
            return "double" if prim_type.name.endswith("64") else "float"
        if prim_type.name == "string":
            return "std::string" if self.use_std else "char*"
        raise Exception(f"{prim_type} not handled")

    def _gen_typename(self, type_obj: BaseType) -> str:
        if isinstance(type_obj, PrimitiveType):
            return self._gen_primitive_typename(type_obj)
        return f"{type_obj.name}"

    def _gen_alias(self, alias_def: AliasDef, *, ctx: GenCtx):
        ref = "*" if alias_def.is_reference else ""
        ctx.add_lines(f"using {alias_def.name} = {self._gen_typename(alias_def.type_obj)}{ref};")

    def _gen_const(self, const_def: ConstantDef, *, ctx: GenCtx):
        cval = (f"{const_def.value}" +
                ("f" if const_def.has_float_value and const_def.resolved_type_obj.name == "float32" else ""))
        ctx.add_lines(f"static constexpr {self._gen_typename(const_def.type_obj)} {const_def.name} = {cval};")

    def _gen_enum_value(self, eval_def: EnumValue, *, ctx: GenCtx, sep: str):
        ctx.add_lines(f"{eval_def.name} = {eval_def.value}{sep}")

    def _gen_enum(self, enum_def: EnumDef, *, ctx: GenCtx, is_forward: bool = False):
        base_type = ""
        if not enum_def.type_obj.is_void:
            base_type = f" : {self._gen_typename(enum_def.type_obj)}"
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

    def _gen_member(self, member_def: MemberDef, *, ctx: GenCtx, is_for_class: bool = True):
        const = "const " if member_def.is_const else ""
        if member_def.is_static and not is_for_class:
            raise Exception(f"{member_def} is static - not supported in POD struct.")
        if member_def.is_static:
            raise Exception("cpp static member generation not implemented yet.")
        if member_def.is_list:
            if self.use_std:
                ctx.add_lines(f"std::vector<{self._gen_typename(member_def.type_obj)}> {member_def.name};")
            else:
                ctx.add_lines([
                    f"{const}{self._gen_typename(member_def.type_obj)}* {member_def.name};",
                    f"{self._gen_typename(get_type('int32'))} {member_def.name}_count;",
                ])
        elif member_def.is_array:
            if self.use_std:
                ctx.add_lines(f"std::array<{self._gen_typename(member_def.type_obj)}, {member_def.array_count}> {member_def.name};")
            else:
                ctx.add_lines(f"{const}{self._gen_typename(member_def.type_obj)} {member_def.name}[{member_def.array_count}];")
        else:
            if self.use_std and member_def.is_string:
                const = ""
            ctx.add_lines(f"{const}{self._gen_typename(member_def.type_obj)} {member_def.name};")

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
        # ctx.add_lines(f"typedef struct {struct_def.name} {struct_def.name};")

    def _gen_param(self, param_def: ParameterDef, sep: str) -> str:
        if param_def.is_list:
            type_str = self._gen_typename(param_def.type_obj)
            if self.use_std:
                return f"const std::vector<{type_str}>& {param_def.name}{sep}"
            return f"const {type_str}* {param_def.name}, {get_type('int32')} {param_def.name}_count{sep}"
        if (param_def.is_string and self.use_std) or not param_def.is_primitive:
            const = "const "
            ref = "&"
        else:
            const = "const " if param_def.is_string else ""
            ref = ""
        return f"{const}{self._gen_typename(param_def.type_obj)}{ref} {param_def.name}{sep}"

    def _gen_method(
            self,
            method_def: MethodDef,
            *,
            class_def: ClassDef,
            ctx: GenCtx,
            is_forward: bool = False,
            is_abstract: bool = False
    ):
        _ = class_def
        if method_def.is_const and method_def.is_static:
            raise ValueError(f"{method_def} can't be both static and const.")
        ref = "*" if method_def.is_reference else ""
        line = [
            # TODO: "<API_NAME>_API" with conditional macro aliasing it to export for impl and import for consumers
            "static " if method_def.is_static else "virtual " if is_abstract else "",
            f"{self._gen_typename(method_def.type_obj)}{ref} {method_def.name}("
        ]
        for (i, param_def) in enumerate(method_def.parameters):
            line.append(
                self._gen_param(
                    param_def,
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

            if class_def.constants:
                for const_def in class_def.constants:
                    self._gen_const(const_def, ctx=ctx)
                ctx.add_lines("")

            ctx.add_lines(f"virtual ~{class_def.name}() = default;")
            for method_def in class_def.methods:
                self._gen_method(method_def, class_def=class_def, ctx=ctx, is_forward=True, is_abstract=is_abstract)

            for member_def in class_def.members:
                self._gen_member(member_def, ctx=ctx)
            ctx.pop_block(public_block)

        ctx.pop_block(class_block)

    def _gen_function(self, func_def: FunctionDef, *, ctx: GenCtx, is_forward: bool = False):
        ref = "*" if func_def.is_reference else ""
        line = [
            f"{self._gen_typename(func_def.type_obj)}{ref} {func_def.name}("
        ]
        for (i, param_def) in enumerate(func_def.parameters):
            line.append(
                self._gen_param(
                    param_def,
                    sep=(", " if i != len(func_def.parameters) - 1 else "")))
        if is_forward:
            line.append(");")
        else:
            raise Exception(f"{func_def}: function body generation not supported.")
        ctx.add_lines("".join(line))


class CBindingGenerator(CppGenerator):
    def __init__(self, api: ApiDef, *, api_h: str):
        super().__init__(api)
        self.api_h = api_h

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        if not (hdr_ctx and src_ctx):
            raise ValueError(f"{self.name} requires both hdr_ctx and src_ctx")
        ctx = hdr_ctx
        self._pragma("once", ctx=ctx)
        self._include("stdlib.h", ctx=ctx)
        ctx.add_lines("")
        ec_block = self._push_extern_c_block(ctx)
        # TODO: insert c wrapper types and protos
        ctx.pop_block(ec_block)

        ctx = src_ctx
        self._include([hdr_ctx.out_path.name, self.api_h], ctx=ctx)
        ctx.add_lines("")
        ec_block = self._push_extern_c_block(ctx)
        # TODO: insert c wrapper types and protos
        ctx.pop_block(ec_block)

    def _gen_alias(self, alias_def: AliasDef, *, ctx: GenCtx):
        ref = "*" if alias_def.is_reference else ""
        ctx.add_lines(f"typedef {self._gen_typename(alias_def.type_obj)}{ref} {alias_def.name};")

    def _gen_param(self, param_def: ParameterDef, sep: str) -> str:
        if param_def.is_list:
            type_str = self._gen_typename(param_def.type_obj)
            return f"const {type_str}* {param_def.name}, {get_type('int32')} {param_def.name}_count{sep}"
        if not param_def.is_primitive:
            const = "const "
            ref = "*"
        else:
            const = "const " if param_def.is_string else ""
            ref = ""
        return f"{const}{self._gen_typename(param_def.type_obj)}{ref} {param_def.name}{sep}"

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


class JniBindingGenerator(CppGenerator):
    def __init__(self, api: ApiDef, *, api_h: str):
        super().__init__(api)
        self.api_h = api_h

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        if hdr_ctx or not src_ctx:
            raise ValueError(f"{self.name} requires src_ctx and does not support hdr_ctx")
        ctx = src_ctx
        self._include([self.api_h, "jni.h"], ctx=ctx)
        ctx.add_lines("")
        ec_block = self._push_extern_c_block(ctx)
        # TODO: jni binding impls
        ctx.pop_block(ec_block)


class KtGenerator(Generator):
    def __init__(self, api: ApiDef):
        super().__init__(api)

    _comment = CppGenerator._comment

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        if hdr_ctx or not src_ctx:
            raise ValueError(f"{self.name} requires src_ctx and does not support hdr_ctx")
        ctx = src_ctx
        ctx.add_lines("import com.google.android.foo")


class SwiftBindingGenerator(CBindingGenerator):
    def __init__(self, api: ApiDef, *, api_h: str):
        super().__init__(api, api_h=api_h)

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        if not (hdr_ctx and src_ctx):
            raise ValueError(f"${self.name} requires both hdr_ctx and src_ctx.")

        ctx = hdr_ctx
        self._pragma("once", ctx=ctx)
        ec_block = self._push_extern_c_block(ctx)
        # TODO: swift binding protos
        ctx.pop_block(ec_block)

        ctx = src_ctx
        self._include(["stdlib.h", hdr_ctx.out_path.name, self.api_h], ctx=ctx)
        ctx.add_lines("")
        ec_block = self._push_extern_c_block(ctx)
        # TODO: swift binding impls
        ctx.pop_block(ec_block)


class SwiftGenerator(Generator):
    def __init__(self, api: ApiDef, api_h: str):
        super().__init__(api)
        self.api_h = api_h

    _comment = CppGenerator._comment

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        if hdr_ctx or not src_ctx:
            raise ValueError(f"{self.name} requires src_ctx and does not support hdr_ctx")
        src_ctx.add_lines("import Foundation")


class WasmBindingGenerator(CppGenerator):
    def __init__(self, api: ApiDef, *, api_h: str):
        super().__init__(api, use_std=True)
        self.api_h = api_h
        self.htype = self._gen_typename(get_type("intptr"))
        self.vtype = self._gen_typename(get_type("void"))

    # https://emscripten.org/docs/porting/connecting_cpp_and_javascript/embind.html
    # look into relaying classes via class binding instead of
    # via opaque reference type (or maybe have option for each depending on classes)
    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        if hdr_ctx or not src_ctx:
            raise ValueError(f"{self.name} requires src_ctx and does not support hdr_ctx")
        ctx = src_ctx
        self._include([self.api_h, "core/core.h", "api/api_util.h", "<emscripten/bind.h>"], ctx=ctx)
        ctx.add_lines("using namespace emscripten;")
        ctx.add_lines(f"using namespace {self.api_ns};\n")
        ctx.add_lines("")
        for class_def in self.api.classes:
            self._gen_class_wrapper(class_def, ctx=ctx)

        self._gen_emscripten_bindings(ctx)

    def _gen_emscripten_bindings(self, ctx: GenCtx):
        ctx.add_lines("")
        bindings_block = ctx.push_block(
            f"EMSCRIPTEN_BINDINGS({self.api.name}) {{",
            post_pop_lines="} // EMSCRIPTEN_BINDINGS",
            indent=True)

        if self.api.structs:
            self._add_comment("structure <-> object bindings", ctx=ctx)
            for struct_def in self.api.structs:
                sd_block = ctx.push_block(
                    f"value_object<{struct_def.name}>(\"{struct_def.name}\")",
                    post_pop_lines=f";\n",
                    indent=True
                )
                for member in struct_def.members:
                    ctx.add_lines(f".field(\"{member.name}\", &{struct_def.name}::{member.name})")
                ctx.pop_block(sd_block)
            ctx.add_lines("")

        if self.api.classes or self.api.functions:
            self._add_comment("method and function bindings", ctx=ctx)
            for class_def in self.api.classes:
                for method in class_def.methods:
                    fname = f"{class_def.name}_{method.name}"
                    ctx.add_lines(f"function(\"{fname}\", &{fname});")
                fname = f"{class_def.name}_destroy"
                ctx.add_lines(f"function(\"{fname}\", &{fname});")

            for func_def in self.api.functions:
                fname = f"{self.api.name}_{func_def.name}"
                ctx.add_lines(f"function(\"{fname}\", &{fname});")
            ctx.add_lines("")

        # complex types used in lists need to be registered
        for lt in [ct for ct in self.api.types_used_in_list if not ct.is_primitive]:
            ctx.add_lines(f"register_vector<{lt.name}>(\"{lt.name}Vector\");")

        ctx.pop_block(bindings_block)

    def _gen_class_wrapper(self, class_def: ClassDef, *, ctx: GenCtx):
        for method in class_def.methods:
            self._gen_method_wrapper(method, class_def=class_def, ctx=ctx)
        self._gen_destroy_wrapper(class_def, ctx=ctx)

    def _gen_destroy_wrapper(self, class_def: ClassDef, *, ctx: GenCtx):
        body_block = ctx.push_block(f"BNG_API_EXPORT {self.vtype} {class_def.name}_destroy({self.htype} handle) {{",
                       post_pop_lines="}", indent=True)
        ctx.add_lines(f"delete ({class_def.name}*)handle;")
        ctx.pop_block(body_block)

    def _gen_method_wrapper(self, method: MethodDef, *, class_def: ClassDef, ctx: GenCtx):
        rtype = self.htype if method.resolved_type_obj is class_def else self._gen_typename(method.type_obj)
        if method.is_reference and method.resolved_type_obj != class_def:
            raise ValueError(f"{class_def} {method} returns raw pointer (unsupported)")
        line = [
            f"BNG_API_EXPORT {rtype} {class_def.name}_{method.name}("
        ]
        params = []
        if not method.is_static:
            params.append(f"{self.htype} handle")
        for param in method.parameters:
            params.append(self._gen_param(param, ""))
        line.extend([", ".join(params), ") {"])
        body_block = ctx.push_block("".join(line), post_pop_lines="}", indent=True)
        args = ", ".join([p.name for p in method.parameters])
        if method.is_static:
            cast = f"({rtype})" if rtype == self.htype else ""
            ctx.add_lines(f"return {cast}{class_def.name}::{method.name}({args});")
        else:
            ctx.add_lines(f"return (({class_def.name}*)handle)->{method.name}({args});")
        ctx.pop_block(body_block)


class JSGenerator(Generator):
    def __init__(self, api: ApiDef, **kwarg):
        super().__init__(api)

    _comment = CppGenerator._comment

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        if hdr_ctx or not src_ctx:
            raise ValueError(f"{self.name} requires src_ctx and does not support hdr_ctx")
        src_ctx.add_lines(self._comment("JS"))

_type_table = {}

def reset_type_table():
    global _type_table
    _type_table = {}

def get_type(name: str) -> BaseType:
    if name not in _type_table:
        raise ValueError(f"type {name} is not in the type table")
    t = _type_table[name]
    return t

def _add_type(typ: BaseType):
    if not isinstance(typ, BaseType):
        raise ValueError(f"{typ} is not a type.")
    if typ.name in _type_table:
        raise ValueError(f"{typ.name} already defined as {_type_table[typ.name]}, can't redefine as {typ}")
    _type_table[typ.name] = typ

def init_type_table():
    reset_type_table()
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
        PrimitiveType(name=base_type)

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
    api_def = ApiDef(**json.loads(api_def.read_text(encoding="utf8")))
    CppGenerator(api_def).generate_files(hdr=out_h)

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
    api_def = ApiDef(**json.loads(api_def.read_text(encoding="utf8")))
    CBindingGenerator(api_def, api_h=api_h).generate_files(hdr=out_h, src=out_cpp)

@app.command
def generate_jni_binding(*, api_def: Path, api_h: str, out_cpp: Path):
    """
    generates JNI binding code

    Parameters
    ----------
    api_def
        api definition json
    api_h
        dependency interface header from generate_cpp_interface
    out_cpp
        output path for generated JNI cpp sourcer
    """
    api_def = ApiDef(**json.loads(api_def.read_text(encoding="utf8")))
    JniBindingGenerator(api_def, api_h=api_h).generate_files(src=out_cpp)

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
    api_def = ApiDef(**json.loads(api_def.read_text(encoding="utf8")))
    KtGenerator(api_def).generate_files(src=out_kt)

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
    api_def = ApiDef(**json.loads(api_def.read_text(encoding="utf8")))
    SwiftBindingGenerator(api_def, api_h=api_h).generate_files(hdr=out_h, src=out_cpp)

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
    api_def = ApiDef(**json.loads(api_def.read_text(encoding="utf8")))
    SwiftGenerator(api_def, api_h=swift_h).generate_files(src=out_swift)

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
    api_def = ApiDef(**json.loads(api_def.read_text(encoding="utf8")))
    WasmBindingGenerator(api_def, api_h=api_h).generate_files(src=out_cpp)

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
    api_def = ApiDef(**json.loads(api_def.read_text(encoding="utf8")))
    JSGenerator(api_def).generate_files(src=out_js)

if __name__ == "__main__":
    app()
