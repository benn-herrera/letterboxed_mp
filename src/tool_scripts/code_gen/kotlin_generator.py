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
    TypedNamed,
    ParameterDef,
    PrimitiveType,
    StructDef,
)
from generator import Generator, GenCtx, BlockCtx
from cpp_generator import CppGenerator


class JniBindingGenerator(CppGenerator):
    generates_header = False
    generates_source = True

    def __init__(self, api: ApiDef, *, gen_version: str, api_h: str, api_pkg: str):
        super().__init__(api, gen_version=gen_version)
        self.api_h = api_h
        self.api_pkg = api_pkg

    def _gen_jni_typename(self, type_obj: BaseType) -> str:
        type_obj = type_obj.resolved_type_obj
        if type_obj.is_primitive:
            if type_obj.is_int:
                return "jlong" if type_obj.name.endswith("64") else "jint"
            if type_obj.is_float:
                return "jdouble" if type_obj.name.endswith("64") else "jfloat"
            if type_obj.is_void:
                return "void"
            if type_obj.is_string:
                return "jstring"
        return ""

    def _gen_jni_param(self, param_def: ParameterDef):
        return f"{self._gen_jni_typename(param_def.type_obj)} {param_def.name}"

    def _gen_jni_method(self, method_def: MethodDef, *, class_def: ClassDef, ctx: GenCtx):
        tn = self._gen_jni_typename(method_def.type_obj)
        params = ["JNIEnv *env", "jobject thiz"]
        params.extend([self._gen_jni_param(p) for p in method_def.parameters])
        params = ", ".join(params)
        block = ctx.push_block(
            f"{tn} BNG_JNI_METHOD({class_def.name}_{method_def.name})({params}) {{",
            post_pop_lines="}",
            indent=True,
        )
        ctx.pop_block(block)

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        ctx = src_ctx
        self._include(
            [self.api_h, "platform/mobile/mobile.h", "jni_util.h", "core/core.h"], ctx=ctx
        )
        ctx.add_lines(
            [
                "",
                "#define BNG_JNI_METHOD(METHOD) JNIEXPORT JNICALL \\",
                f"  Java_{self.api_pkg.replace('.', '_')}_##METHOD",
            ]
        )

        ec_block = self._push_extern_c_block(ctx)
        for class_def in self.api.classes:
            self._gen_class_binding(class_def, ctx=ctx)
        ctx.pop_block(ec_block)

    def _gen_class_binding(self, class_def: ClassDef, ctx: GenCtx):
        for method_def in class_def.methods:
            self._gen_jni_method(method_def, class_def=class_def, ctx=ctx)


class KtGenerator(Generator):
    generates_header = False
    generates_source = True

    def __init__(self, api: ApiDef, *, gen_version: str):
        super().__init__(api, gen_version=gen_version)

    _comment = CppGenerator._comment

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        ctx = src_ctx
        # ctx.add_lines("import com.google.android.foo")

        # if self.api.aliases:
        #     for alias_def in self.api.aliases:
        #         self._gen_alias(alias_def, ctx=ctx)
        #     ctx.add_lines("")

        if self.api.constants:
            for const_def in self.api.constants:
                self._gen_const(const_def, ctx=ctx)
            ctx.add_lines("")

        for enum_def in self.api.enums:
            self._gen_enum(enum_def, ctx=ctx)

        for struct_def in self.api.structs:
            self._gen_struct(struct_def, ctx=ctx)

        for class_def in self.api.classes:
            self._gen_class(class_def, ctx=ctx)

        # for function_def in self.api.functions:
        #     self._gen_function(function_def, ctx=ctx)

    def _gen_const(self, const_def: ConstantDef, *, ctx: GenCtx):
        pass

    def _gen_enum(self, enum_def: EnumDef, *, ctx: GenCtx):
        for enum_value in enum_def.members:
            self._gen_enum_value(enum_value, ctx=ctx)

    def _gen_enum_value(self, enum_value: EnumValue, *, ctx: GenCtx):
        pass

    def _gen_struct(self, struct_def: StructDef, *, ctx: GenCtx):
        s_block = ctx.push_block(f"struct {struct_def.name} {{", post_pop_lines="}", indent=True)
        for member_def in struct_def.members:
            self._gen_member(member_def, ctx=ctx)
        ctx.pop_block(s_block)

    def _gen_member(self, member_def: MemberDef, *, ctx: GenCtx):
        ctx.add_lines(["@JvmField", f"var {member_def.name}: {self._gen_type(member_def)}"])

    def _gen_class(self, class_def: ClassDef, *, ctx: GenCtx):
        c_block = ctx.push_block(f"class {class_def.name} {{", post_pop_lines="}", indent=True)
        for method_def in class_def.methods:
            self._gen_method(method_def, class_def=class_def, ctx=ctx)
        ctx.pop_block(c_block)

    def _gen_method(self, method_def: MethodDef, *, class_def: ClassDef, ctx: GenCtx):
        _ = class_def
        params = ", ".join([self._gen_param(p) for p in method_def.parameters])
        ctx.add_lines(f"external fun {method_def.name}({params}): {self._gen_type(method_def)}")

    def _gen_param(self, param_def: ParameterDef) -> str:
        return f"{param_def.name}: {self._gen_type(param_def)}"

    def _gen_type(self, typed: TypedNamed) -> str:
        base_type = self._gen_base_type(typed.type_obj)
        if typed.is_list:
            return f"List<{base_type}>"
        if typed.is_array:
            return f"Array<{base_type}, {typed.array_count}>"
        return base_type

    def _gen_base_type(self, type_obj: BaseType) -> str:
        if type_obj.is_void:
            return "Unit"
        if type_obj.is_string:
            return "String"
        if type_obj.is_int or type_obj.is_float:
            return type_obj.name
        return type_obj.name
