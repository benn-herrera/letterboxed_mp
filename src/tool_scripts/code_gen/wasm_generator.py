from typing import Optional
from api_def import (
    ApiDef, AliasDef, BaseType, ClassDef, ConstantDef, EnumDef, EnumValue, FunctionDef,
    MemberDef, MethodDef, ParameterDef, PrimitiveType, StructDef, get_type
)
from generator import (Generator, GenCtx, BlockCtx)
from cpp_generator import CppGenerator

class WasmBindingGenerator(CppGenerator):
    def __init__(self, api: ApiDef, *, gen_version: str, api_h: str):
        super().__init__(api, gen_version=gen_version, use_std=True)
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
        ctx.add_lines([
            f"using namespace {self.api_ns};",
            ""
        ])
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
                    f"emscripten::value_object<{struct_def.name}>(\"{struct_def.name}\")",
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
                    return_value_policy="" if (method.is_primitive and not method.is_string) \
                        else ", return_value_policy::take_ownership()"
                    ctx.add_lines(f"emscripten::function(\"{fname}\", &{fname}{return_value_policy});")
                fname = f"{class_def.name}_destroy"
                ctx.add_lines(f"emscripten::function(\"{fname}\", &{fname});")

            for func_def in self.api.functions:
                fname = f"{self.api.name}_{func_def.name}"
                return_value_policy = "" if (func_def.is_primitive and not func_def.is_string) \
                    else ", return_value_policy::take_ownership()"
                ctx.add_lines(f"emscripten::function(\"{fname}\", &{fname}{return_value_policy});")
            ctx.add_lines("")

        if self.api.types_used_in_list or self.api.type_array_counts:
            self._add_comment("register list and array usages", ctx=ctx)
            for lt in self.api.types_used_in_list:
                ltn = self._gen_typename(lt)
                ctx.add_lines(f"emscripten::register_vector<{ltn}>(\"{ltn}Vector\");")
            for (at, counts) in self.api.type_array_counts.items():
                atn = self._gen_typename(at)
                for count in counts:
                    array_block = ctx.push_block(
                        f"emscripten::value_array<std::array<{atn}, {count}>>(\"array_{at.name}_{count}\")",
                        post_pop_lines=";",
                        indent=True)
                    for i in range(count):
                        ctx.add_lines(f".element(emscripten::index<{i}>())")
                    ctx.pop_block(array_block)

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
    def __init__(self, api: ApiDef, *, gen_version: str):
        super().__init__(api, gen_version=gen_version)

    _comment = CppGenerator._comment

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        if hdr_ctx or not src_ctx:
            raise ValueError(f"{self.name} requires src_ctx and does not support hdr_ctx")
        src_ctx.add_lines(self._comment("JS"))
