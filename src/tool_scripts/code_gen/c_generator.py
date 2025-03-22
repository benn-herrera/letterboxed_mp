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
    PrimitiveType,
    RefType,
    StructDef,
    get_type,
    ensure_snake,
)
from generator import Generator, GenCtx, BlockCtx
from cpp_generator import CppGenerator


class CBindingGenerator(CppGenerator):
    generates_header = True
    generates_source = True

    def __init__(self, api: ApiDef, *, gen_version: str, api_h: str):
        super().__init__(api, gen_version=gen_version)
        self.api_h = api_h

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        if hdr_ctx is not None:
            ctx = hdr_ctx
            self._pragma("once", ctx=ctx)
            self._include("stdlib.h", ctx=ctx)
            ctx.add_lines("")
            ec_block = self._push_extern_c_block(ctx)
            for enum_def in self.api.enums:
                self._gen_enum(enum_def, ctx=ctx)
            for struct_def in self.api.structs:
                self._gen_struct(struct_def, ctx=ctx)
            for class_def in self.api.classes:
                self._gen_class_decls(class_def, ctx=ctx)
            ctx.pop_block(ec_block)

        if src_ctx is not None:
            ctx = src_ctx
            self._include([hdr_ctx.out_path.name, self.api_h], ctx=ctx)
            ctx.add_lines("")
            ec_block = self._push_extern_c_block(ctx)
            for class_def in self.api.classes:
                self._gen_class_impls(class_def, ctx=ctx)
            ctx.pop_block(ec_block)

    def _gen_alias(self, alias_def: AliasDef, *, ctx: GenCtx):
        ref = "*" if alias_def.ref_type else ""
        ctx.add_lines(f"typedef {self._gen_typename(alias_def.type_obj)}{ref} {alias_def.name};")

    def _gen_param(self, param_def: ParameterDef) -> str:
        if param_def.is_list:
            type_str = self._gen_typename(param_def.type_obj)
            count_type_str = self._gen_typename(get_type("uint32"))
            return f"const {type_str}* {param_def.name}, {count_type_str} {param_def.name}_count"
        if not param_def.is_primitive:
            const = "const "
            ref = "*"
        else:
            const = "const " if param_def.is_string else ""
            ref = ""
        return f"{const}{self._gen_typename(param_def.type_obj)}{ref} {param_def.name}"

    def _gen_c_enum_value(self, eval_def: EnumValue, *, pfx: str, ctx: GenCtx, sep: str):
        ctx.add_lines(f"{pfx}{eval_def.name} = {eval_def.value}{sep}")

    def _gen_enum(self, enum_def: EnumDef, *, ctx: GenCtx, is_forward: bool = False):
        enum_decl = f"enum {enum_def.name}"
        if is_forward or not enum_def.members:
            ctx.add_lines([f"{enum_decl};" f"typedef {enum_decl} {enum_def.name};"])
            return
        enum_block = ctx.push_block(f"{enum_decl} {{", indent=True, post_pop_lines="};")
        enum_pfx = self._enum_value_prefix(enum_def)
        for i, eval_def in enumerate(enum_def.members):
            self._gen_c_enum_value(
                eval_def, ctx=ctx, pfx=enum_pfx, sep=("," if i != len(enum_def.members) - 1 else "")
            )
        ctx.pop_block(enum_block)
        ctx.add_lines(
            [
                f"typedef {enum_decl} {enum_def.name};",
                "",
            ]
        )

    @staticmethod
    def _enum_value_prefix(enum_def: EnumDef) -> str:
        return "".join([c for c in enum_def.name if c.isupper()]) + "_"

    def _gen_struct(self, struct_def: StructDef, *, ctx: GenCtx, is_forward: bool = False):
        term = ";" if is_forward else " {"
        struct_decl = f"struct {struct_def.name}{term}"
        struct_block = ctx.push_block(
            struct_decl, indent=True, post_pop_lines=("};" if not is_forward else None)
        )
        if not is_forward:
            for member_def in struct_def.members:
                self._gen_c_member(member_def, ctx=ctx)
        ctx.pop_block(struct_block)
        ctx.add_lines(
            [
                f"typedef struct {struct_def.name} {struct_def.name};",
                "",
            ]
        )

    def _gen_c_member(self, member_def: MemberDef, *, ctx: GenCtx):
        if member_def.is_static:
            raise Exception(f"{member_def} is static - not supported in POD struct.")
        const = "const " if member_def.is_const else ""
        ref = "*" if member_def.ref_type else ""
        type_spec = f"{self._gen_typename(member_def.type_obj)}{ref}"
        if member_def.is_array:
            type_spec = f"{type_spec}[{member_def.array_count}]"
        if member_def.is_list:
            count_type_str = self._gen_typename(get_type("uint32"))
            return ctx.add_lines(
                [
                    f"{const}{type_spec}* {member_def.name};",
                    f"{count_type_str} {member_def.name}_count;",
                ]
            )
        return ctx.add_lines(f"{const}{type_spec} {member_def.name};")

    def _gen_typename(self, type_obj: BaseType) -> str:
        if type_obj.is_primitive:
            if type_obj.name == "string":
                return "char*"
            return super()._gen_typename(type_obj)
        return f"{type_obj.name}"

    def _gen_class_decls(self, class_def: ClassDef, *, ctx: GenCtx):
        self._gen_class_opaque_type(class_def, ctx=ctx)
        for method_def in class_def.methods:
            self._gen_class_method_decl(method_def, class_def=class_def, ctx=ctx)

    # def _gen_constructor_destructor_decls(self, class_def: ClassDef, *, ctx: GenCtx):
    #     self._add_comment(f"{class_def.name} life cycle", ctx=ctx)
    #     snake_name = ensure_snake(class_def.name)
    #     ctx.add_lines(
    #         [
    #             f"{class_def.name}* create_{snake_name}();",
    #             f"void destroy_{snake_name}({class_def.name}*);",
    #             "",
    #         ]
    #     )

    def _gen_class_opaque_type(self, class_def: ClassDef, *, ctx: GenCtx):
        ctx.add_lines(
            [
                f"struct {class_def.name};",
                f"typedef struct {class_def.name} {class_def};",
                "",
            ]
        )

    def _gen_class_method_decl(self, method_def: MethodDef, *, class_def: ClassDef, ctx: GenCtx):
        pass

    def _gen_class_impls(self, class_def: ClassDef, *, ctx: GenCtx):
        pass
