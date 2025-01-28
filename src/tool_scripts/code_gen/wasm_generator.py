from typing import Optional
from api_def import (
    ApiDef, AliasDef, BaseType, ClassDef, ConstantDef, EnumDef, EnumValue, FunctionDef,
    MemberDef, MethodDef, ParameterDef, PrimitiveType, StructDef, get_type
)
from generator import (Generator, GenCtx, BlockCtx)
from cpp_generator import CppGenerator

class WasmBindingGenerator(CppGenerator):
    generates_header = False
    generates_source = True

    def __init__(self, api: ApiDef, *, gen_version: str, api_h: str):
        super().__init__(api, gen_version=gen_version)
        self.api_h = api_h

    # https://emscripten.org/docs/porting/connecting_cpp_and_javascript/embind.html
    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        ctx = src_ctx
        self._include([self.api_h, "core/core.h", "api/api_util.h", "<emscripten/bind.h>"], ctx=ctx)
        ctx.add_lines([
            f"using namespace {self.api_ns};",
            ""
        ])
        bindings_block = ctx.push_block(
            f"EMSCRIPTEN_BINDINGS({self.api.name}) {{",
            post_pop_lines="} // EMSCRIPTEN_BINDINGS",
            indent=True)

        self._gen_struct_bindings(ctx=ctx)
        self._gen_class_bindings(ctx=ctx)
        self._gen_function_bindings(ctx=ctx)
        self._gen_collection_registration(ctx=ctx)

        ctx.pop_block(bindings_block)

    def _gen_struct_bindings(self, *, ctx: GenCtx):
        if self.api.structs:
            self._add_comment("structure <-> object bindings", ctx=ctx)
            for struct_def in self.api.structs:
                self._gen_struct_binding(struct_def, ctx=ctx)
            ctx.add_lines("")

    def _gen_struct_binding(self, struct_def: StructDef, *, ctx: GenCtx):
        sd_block = ctx.push_block(
            f"emscripten::value_object<{struct_def.name}>(\"{struct_def.name}\")",
            post_pop_lines=f";",
            indent=True
        )
        for member in struct_def.members:
            ctx.add_lines(f".field(\"{member.name}\", &{struct_def.name}::{member.name})")
        ctx.pop_block(sd_block)

    def _gen_class_bindings(self, *, ctx: GenCtx):
        if self.api.classes:
            self._add_comment("class bindings", ctx=ctx)
            for class_def in self.api.classes:
                self._gen_class_binding(class_def, ctx=ctx)

    def _gen_class_binding(self, class_def: ClassDef, *, ctx: GenCtx):
        factory = class_def.static_factory
        if factory:
            factory = f"{class_def.name}::{factory.name}"
        else:
            factory = next(
                (f.name for f in self.api.functions if f.is_factory and f.resolved_type_obj is class_def),
                None
            )
        class_block = ctx.push_block(
            f"emscripten::class_<{class_def.name}>(\"{class_def.name}\")",
            post_pop_lines=";",
            indent=True)

        if factory:
            ctx.add_lines(f".constructor(&{factory},  emscripten::return_value_policy::take_ownership())")
        else:
            # TODO: constructors?
            constructor_param_types = []
            constructor_param_types = ", ".join(constructor_param_types)
            ctx.add_lines(f".constructor<{constructor_param_types}>()")

        for method in class_def.methods:
            self._gen_method_binding(method, class_def=class_def, ctx=ctx)

        ctx.pop_block(class_block)

    def _gen_method_binding(self, method: MethodDef, class_def: ClassDef, ctx: GenCtx):
        if method.is_static:
            if not method.is_factory:
                raise Exception(f"binding static method {class_def.name}::{method.name} not supported.")
            return
        return_value_policy = "" if (method.is_primitive and not method.is_string) \
            else ", emscripten::return_value_policy::take_ownership()"
        ctx.add_lines(
            f".function(\"{method.name}\", &{class_def.name}::{method.name}{return_value_policy})"
        )

    def _gen_function_bindings(self, *, ctx: GenCtx):
        if self.api.functions:
            self._add_comment("function bindings", ctx=ctx)
            for func_def in self.api.functions:
                self._gen_func_binding(func_def, ctx=ctx)

    def _gen_func_binding(self, func_def: FunctionDef, *, ctx: GenCtx):
        fname = f"{self.api.name}_{func_def.name}"
        return_value_policy = "" if (func_def.is_primitive and not func_def.is_string) \
            else ", emscripten::return_value_policy::take_ownership()"
        ctx.add_lines(f"emscripten::function(\"{fname}\", &{fname}{return_value_policy});")

    def _gen_collection_registration(self, *, ctx: GenCtx):
        if self.api.types_used_in_list or self.api.type_array_counts:
            if used_in_list := self.api.types_used_in_list:
                ctx.add_lines("")
                self._add_comment("register list usages", ctx=ctx)
                for lt in used_in_list:
                    ltn = self._gen_typename(lt)
                    ctx.add_lines(f"emscripten::register_vector<{ltn}>(\"{ltn}Vector\");")

            if self.api.type_array_counts:
                ctx.add_lines("")
                self._add_comment("register array usages", ctx=ctx)
                for (at, counts) in self.api.type_array_counts.items():
                    atn = self._gen_typename(at)
                    for count in counts:
                        array_decl = f"emscripten::value_array<std::array<{atn}, {count}>>(\"array_{at.name}_{count}\")"
                        array_block = ctx.push_block(
                            array_decl,
                            post_pop_lines=";",
                            indent=True)
                        for i in range(count):
                            ctx.add_lines(f".element(emscripten::index<{i}>())")
                        ctx.pop_block(array_block)
