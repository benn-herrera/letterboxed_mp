from typing import Optional
from api_def import (
    ApiDef, AliasDef, BaseType, ClassDef, ConstantDef, EnumDef, EnumValue, FunctionDef,
    MemberDef, MethodDef, ParameterDef, PrimitiveType, StructDef, get_type
)
from generator import (Generator, GenCtx, BlockCtx)

class CppGenerator(Generator):
    def __init__(self, api: ApiDef, *, gen_version: str, use_std: bool=True):
        super().__init__(api, gen_version=gen_version)
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
