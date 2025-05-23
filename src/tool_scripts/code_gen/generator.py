import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Tuple
from api_def import ApiDef


class BlockCtx:
    def __init__(
        self,
        push_lines: Optional[str],
        *,
        indent: bool = False,
        pre_pop_lines: Optional[Any] = None,
        post_pop_lines: Optional[Any] = None,
        on_pre_pop: Optional[callable] = None,
        on_post_pop: Optional[callable] = None,
    ):
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
            raise Exception(
                f"expected current indent {expected_cur_indent} but it is {self._indent_count}"
            )
        self._indent_count -= 1

    def push_block(
        self,
        push_lines: Optional[str],
        *,
        indent: bool = False,
        pre_pop_lines: Optional[Any] = None,
        post_pop_lines: Optional[Any] = None,
        on_pre_pop: Optional[callable] = None,
        on_post_pop: Optional[callable] = None,
    ) -> BlockCtx:
        # not using *args and **kwargs for IDE code completion mercy
        block = BlockCtx(
            push_lines,
            indent=indent,
            pre_pop_lines=pre_pop_lines,
            post_pop_lines=post_pop_lines,
            on_pre_pop=on_pre_pop,
            on_post_pop=on_post_pop,
        )
        if block.push_lines is not None:
            self.add_lines(block.push_lines)
        if block.indent:
            block.block_indent = self.push_indent()
        self._block_ctx_stack.append(block)
        return self._block_ctx_stack[-1]

    def pop_block(self, expected_block: BlockCtx):
        if not self._block_ctx_stack:
            raise Exception("ctx stack is empty")
        block = self._block_ctx_stack.pop(-1)
        if expected_block is not block:
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
            lines = lines.split("\n")
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
    generates_header = False
    generates_source = False

    def __init__(self, api: ApiDef, *, gen_version: str):
        self.api = api
        self.gen_version = gen_version

    @property
    def name(self):
        return self.__class__.__name__

    def _comment(self, text: str) -> [str]:
        raise Exception(f"_comment not implemented in {self.name}")

    def _generate(self, *, src_ctx: Optional[GenCtx], hdr_ctx: Optional[GenCtx]):
        raise Exception(f"_generate_api not implemented in {self.name}")

    def _add_comment(self, text: str, ctx: GenCtx):
        ctx.add_lines(self._comment(text))

    def generate_ctx(
        self, *, hdr: Optional[Path] = None, src: Optional[Path] = None
    ) -> Tuple[Optional[GenCtx], Optional[GenCtx]]:
        if hdr and not self.generates_header:
            raise Exception(
                f"{self.name} does not generate a header file but hdr path was specified"
            )
        if self.generates_header and not hdr:
            raise Exception(f"{self.name} generates a header file but hdr path was not specified")
        if src and not self.generates_source:
            raise Exception(
                f"{self.name} does not generate a source file but src path was specified"
            )
        if self.generates_source and not src:
            raise Exception(f"{self.name} generates a source file but src path was not specified")

        def make_ctx(out_path: Optional[Path]) -> Optional[GenCtx]:
            ctx = GenCtx(out_path) if out_path else None
            if ctx:
                self._add_comment(
                    f"\n{ctx.out_path.name} v{self.api.version} generated by {self.gen_version} {datetime.now()}\n",
                    ctx=ctx,
                )
            return ctx

        hdr_ctx, src_ctx = make_ctx(hdr), make_ctx(src)
        self._generate(hdr_ctx=hdr_ctx, src_ctx=src_ctx)
        return hdr_ctx, src_ctx

    def generate_files(self, *, hdr: Optional[Path] = None, src: Optional[Path] = None):
        for ctx in self.generate_ctx(hdr=hdr, src=src):
            if ctx:
                os.makedirs(ctx.out_path.parent.as_posix(), exist_ok=True)
                ctx.out_path.write_text(ctx.get_gen_text(), encoding="utf-8", newline="\n")
