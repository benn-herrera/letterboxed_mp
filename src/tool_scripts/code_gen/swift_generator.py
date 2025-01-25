from typing import Optional
from api_def import (
    ApiDef, AliasDef, BaseType, ClassDef, ConstantDef, EnumDef, EnumValue, FunctionDef,
    MemberDef, MethodDef, ParameterDef, PrimitiveType, StructDef, get_type
)
from generator import (Generator, GenCtx, BlockCtx)
from c_generator import CBindingGenerator

class SwiftBindingGenerator(CBindingGenerator):
    def __init__(self, api: ApiDef, *, gen_version: str, api_h: str):
        super().__init__(api, gen_version=gen_version, api_h=api_h)

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
    def __init__(self, api: ApiDef, *, gen_version: str, api_h: str):
        super().__init__(api, gen_version=gen_version)
        self.api_h = api_h

    _comment = CBindingGenerator._comment

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        if hdr_ctx or not src_ctx:
            raise ValueError(f"{self.name} requires src_ctx and does not support hdr_ctx")
        src_ctx.add_lines("import Foundation")
