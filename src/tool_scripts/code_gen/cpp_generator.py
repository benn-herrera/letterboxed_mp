from typing import Optional
from api_def import (
    ApiDef,
    AliasDef,
    BaseType,
    ClassDef,
    ConstantDef,
    EnumDef,
    EnumValue,
    FunctionDef,
    MemberDef,
    MethodDef,
    ParameterDef,
    RefType,
    StructDef,
    TypedNamed,
)
from generator import Generator, GenCtx, BlockCtx


class CppGenerator(Generator):
    generates_header = True
    generates_source = False

    def __init__(self, api: ApiDef, *, gen_version: str):
        super().__init__(api, gen_version=gen_version)

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        ctx = hdr_ctx
        self._pragma("once", ctx=ctx)
        self._include(["array", "memory", "string", "vector", "api/api_util.h"], ctx=ctx)

        ns_block = ctx.push_block(
            f"\nnamespace {self.api_ns} {{",
            indent=True,
            post_pop_lines=f"}} // namespace {self.api_ns}",
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
        return ctx.push_block(
            f"#if defined({symbol})", post_pop_lines=f"#endif // defined({symbol})"
        )

    def _push_extern_c_block(self, ctx: GenCtx) -> BlockCtx:
        def on_post_pop():
            ctx.add_lines("")
            block = self._push_ifdef_block("__cplusplus", ctx=ctx)
            ctx.add_lines('} // extern "C"')
            ctx.pop_block(block)

        ec_block = ctx.push_block(None, on_pre_pop=on_post_pop)

        ifdef_block = self._push_ifdef_block("__cplusplus", ctx=ctx)
        ctx.add_lines('extern "C" {')
        ctx.pop_block(ifdef_block)
        ctx.add_lines("")
        return ec_block

    @staticmethod
    def _is_sys_header(hname: str) -> bool:
        return ("." not in hname) or hname.startswith("std")

    @staticmethod
    def _enclosed_hname(hname: str) -> str:
        if '"' in hname or "<" in hname:
            return hname
        return f"<{hname}>" if CppGenerator._is_sys_header(hname) else f'"{hname}"'

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

    def _gen_typename(self, type_obj: BaseType) -> str:
        if type_obj.is_primitive:
            if type_obj.name in ["void", "bool"]:
                return type_obj.name
            if type_obj.is_int:
                return f"{type_obj.name}_t"
            if type_obj.is_float:
                return "double" if type_obj.name.endswith("64") else "float"
            if type_obj.name == "string":
                return "std::string"
            raise ValueError(f"{type_obj} not handled.")
        return f"{type_obj.name}"

    def _gen_alias(self, alias_def: AliasDef, *, ctx: GenCtx):
        if (
            alias_def.ref_type is None
            or alias_def.ref_type == RefType.raw
            or alias_def.ref_type == RefType.non_optional
        ):
            const = "const " if alias_def.is_const else ""
            ref = alias_def.ref_type or ""
            type_spec = f"{const}{self._gen_typename(alias_def.type_obj)}{ref}"
        else:
            type_spec = f"std::{alias_def.ref_type}<{self._gen_typename(alias_def.type_obj)}>"
        if alias_def.is_array:
            type_spec = f"std::array<{type_spec}, {alias_def.array_count}>"
        elif alias_def.is_list:
            type_spec = f"std::vector<{type_spec}>"
        ctx.add_lines(f"using {alias_def.name} = {type_spec};")

    def _gen_const(self, const_def: ConstantDef, *, ctx: GenCtx):
        cval = f"{const_def.value}" + (
            "f"
            if const_def.has_float_value and const_def.resolved_type_obj.name == "float32"
            else ""
        )
        ctx.add_lines(
            f"static constexpr {self._gen_typename(const_def.type_obj)} {const_def.name} = {cval};"
        )

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
            post_pop_lines="};\n" if not is_forward else None,
        )
        if not is_forward:
            for i, eval_def in enumerate(enum_def.members):
                self._gen_enum_value(
                    eval_def, ctx=ctx, sep=("," if i != len(enum_def.members) - 1 else "")
                )
        ctx.pop_block(enum_block)

    def _gen_member(self, member_def: MemberDef, *, ctx: GenCtx, is_for_class: bool = True):
        if member_def.is_static and not is_for_class:
            raise Exception(f"{member_def} is static - not supported in POD struct.")
        if member_def.is_static:
            raise Exception("cpp static member generation not implemented.")
        const = "const " if member_def.is_const else ""
        if (
            member_def.ref_type is None
            or member_def.ref_type == RefType.raw
            or member_def.ref_type == RefType.non_optional
        ):
            ref = member_def.ref_type or ""
            type_spec = f"{self._gen_typename(member_def.type_obj)}{ref}"
            if ref and (member_def.is_array or member_def.is_list):
                type_spec = f"{const}{type_spec}"
                const = ""
        else:
            type_spec = (
                f"std::<{member_def.ref_type}_ptr>{self._gen_typename(member_def.type_obj)}>"
            )
        if member_def.is_array:
            type_spec = f"std::array<{type_spec},{member_def.array_count}>"
        elif member_def.is_list:
            type_spec = f"std::vector<{type_spec}>"
        return ctx.add_lines(f"{const}{type_spec} {member_def.name};")

    def _gen_struct(self, struct_def: StructDef, *, ctx: GenCtx, is_forward: bool = False):
        term = ";" if is_forward else " {"
        struct_decl = f"struct {struct_def.name}{term}"
        struct_block = ctx.push_block(
            struct_decl, indent=True, post_pop_lines=("};\n" if not is_forward else None)
        )
        if not is_forward:
            for member_def in struct_def.members:
                self._gen_member(member_def, ctx=ctx)
        ctx.pop_block(struct_block)

    def _gen_param(self, param_def: ParameterDef) -> str:
        const = "const " if param_def.is_const else ""
        if (
            param_def.ref_type is None
            or param_def.ref_type == RefType.raw
            or param_def.ref_type == RefType.non_optional
        ):
            ref = param_def.ref_type or ""
            if (param_def.is_array or param_def.is_list) and ref == RefType.non_optional:
                ref = ""
            type_spec = f"{self._gen_typename(param_def.type_obj)}{ref}"
        else:
            type_spec = f"std::{param_def.ref_type}_ptr<{self._gen_typename(param_def.type_obj)}>"

        if param_def.is_array:
            type_spec = f"std::array<{type_spec}, {param_def.array_count}>&"
        elif param_def.is_list:
            type_spec = f"std::vector<{type_spec}>&"
        elif param_def.is_string or (
            param_def.ref_type is not None
            and param_def.ref_type != RefType.raw
            and param_def.ref_type != RefType.non_optional
        ):
            type_spec = f"{type_spec}&"
        return f"{const}{type_spec} {param_def.name}"

    def _gen_method(
        self,
        method_def: MethodDef,
        *,
        class_def: ClassDef,
        ctx: GenCtx,
        is_forward: bool = False,
        is_abstract: bool = False,
    ):
        _ = class_def
        if not is_forward:
            raise Exception(f"{method_def}: method body generation not supported.")
        # TODO: "<API_NAME>_API" with conditional macro aliasing it to export for impl and import for consumers
        decorator = "static " if method_def.is_static else "virtual " if is_abstract else ""
        if (
            method_def.ref_type is None
            or method_def.ref_type == RefType.raw
            or method_def.ref_type == RefType.non_optional
        ):
            ref = method_def.ref_type or ""
            type_spec = f"{self._gen_typename(method_def.type_obj)}{ref}"
        else:
            type_spec = f"std::{method_def.ref_type}_ptr<{self._gen_typename(method_def.type_obj)}>"
        if method_def.is_array:
            type_spec = f"std::array<{type_spec}, {method_def.array_count}>"
        elif method_def.is_list:
            type_spec = f"std::vector<{type_spec}>"
        if (
            method_def.is_array or method_def.is_list
        ) and method_def.ref_type == RefType.non_optional:
            const = "const " if method_def.is_const else ""
            type_spec = f"{const}{type_spec}&"

        decl = f"{decorator}{type_spec} {method_def.name}"
        params = ", ".join([self._gen_param(param_def) for param_def in method_def.parameters])
        decorator = " const" if method_def.is_const else ""
        abstract = " = 0" if is_abstract and not method_def.is_static else ""
        ctx.add_lines(f"{decl}({params}){decorator}{abstract};")

    def _gen_class(
        self,
        class_def: ClassDef,
        *,
        ctx: GenCtx,
        is_forward: bool = False,
        is_abstract: bool = False,
    ):
        term = ";" if is_forward else " {"
        class_decl = f"class {class_def.name}{term}"
        class_block = ctx.push_block(class_decl, post_pop_lines="};\n" if not is_forward else None)

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
                self._gen_method(
                    method_def,
                    class_def=class_def,
                    ctx=ctx,
                    is_forward=True,
                    is_abstract=is_abstract,
                )

            for member_def in class_def.members:
                self._gen_member(member_def, ctx=ctx)
            ctx.pop_block(public_block)

        ctx.pop_block(class_block)

    def _gen_function(self, func_def: FunctionDef, *, ctx: GenCtx, is_forward: bool = False):
        if not is_forward:
            raise Exception(f"{func_def}: function body generation not supported.")
        if (
            func_def.ref_type is None
            or func_def.ref_type == RefType.raw
            or func_def.ref_type == RefType.non_optional
        ):
            ref = func_def.ref_type or ""
            type_spec = f"{self._gen_typename(func_def.type_obj)}{ref}"
        else:
            type_spec = f"std::{func_def.ref_type}_ptr<{self._gen_typename(func_def.type_obj)}>"
        if func_def.is_array:
            type_spec = f"std::array<{type_spec}, {func_def.array_count}>"
        elif func_def.is_list:
            type_spec = f"std::vector<{type_spec}>"
        if (func_def.is_array or func_def.is_list) and func_def.ref_type == RefType.non_optional:
            const = "const " if func_def.is_const else ""
            type_spec = f"{const}{type_spec}&"

        decl = f"{type_spec} {func_def.name}"
        params = ", ".join([self._gen_param(param_def) for param_def in func_def.parameters])
        ctx.add_lines(f"{decl}({params});")
