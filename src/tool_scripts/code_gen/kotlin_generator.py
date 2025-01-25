from typing import Optional
from api_def import (
    ApiDef, AliasDef, BaseType, ClassDef, ConstantDef, EnumDef, EnumValue, FunctionDef,
    MemberDef, MethodDef, ParameterDef, PrimitiveType, StructDef, get_type
)
from generator import (Generator, GenCtx, BlockCtx)
from cpp_generator import CppGenerator

class JniBindingGenerator(CppGenerator):
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

    def _gen_jni_method(
            self,
            method_def: MethodDef,
            *,
            class_def: ClassDef,
            ctx: GenCtx
    ):
        tn = self._gen_jni_typename(method_def.type_obj)
        params = ["JNIEnv *env", "jobject thiz"]
        for param_def in method_def.parameters:
            params.append(self._gen_jni_param(param_def))
        params = ", ".join(params)
        block = ctx.push_block(f"{tn} BNG_JNI_METHOD({class_def.name}_{method_def.name})({params}) {{", post_pop_lines="}", indent=True)
        ctx.pop_block(block)

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        if hdr_ctx or not src_ctx:
            raise ValueError(f"{self.name} requires src_ctx and does not support hdr_ctx")
        ctx = src_ctx
        self._include([
            self.api_h,
            "platform/mobile/mobile.h",
            "jni_util.h",
            "core/core.h"
        ], ctx=ctx)
        ctx.add_lines([
            "",
            "#define BNG_JNI_METHOD(METHOD) JNIEXPORT JNICALL \\",
            f"  Java_{self.api_pkg.replace('.', '_')}_##METHOD"
        ])

        ec_block = self._push_extern_c_block(ctx)
        for class_def in self.api.classes:
            for method_def in class_def.methods:
                self._gen_jni_method(method_def, class_def=class_def, ctx=ctx)
        ctx.pop_block(ec_block)


class KtGenerator(Generator):
    def __init__(self, api: ApiDef, *, gen_version: str):
        super().__init__(api, gen_version=gen_version)

    _comment = CppGenerator._comment

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        if hdr_ctx or not src_ctx:
            raise ValueError(f"{self.name} requires src_ctx and does not support hdr_ctx")
        ctx = src_ctx
        ctx.add_lines("import com.google.android.foo")
