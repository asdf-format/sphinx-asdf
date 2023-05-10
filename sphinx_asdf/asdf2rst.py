import codecs
import io
import os
import tempfile
import textwrap

import asdf
from asdf import AsdfFile, versioning
from asdf.constants import ASDF_MAGIC, ASDF_STANDARD_COMMENT, BLOCK_FLAG_STREAMED
from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.util.nodes import set_source_info

version_string = str(versioning.default_version)
TMPDIR = tempfile.mkdtemp()
GLOBALS = {}
FLAGS = {BLOCK_FLAG_STREAMED: "BLOCK_FLAG_STREAMED"}


class RunCodeDirective(Directive):
    has_content = True
    optional_arguments = 1

    def run(self):
        code = textwrap.dedent("\n".join(self.content))

        cwd = os.getcwd()
        os.chdir(TMPDIR)

        try:
            try:
                exec(code, GLOBALS)
            except Exception:
                print(code)
                raise

            literal = nodes.literal_block(code, code)
            literal["language"] = "python"
            set_source_info(self, literal)
        finally:
            os.chdir(cwd)

        if "hidden" not in self.arguments:
            return [literal]
        else:
            return []


class AsdfDirective(Directive):
    required_arguments = 1
    optional_arguments = 1

    def run(self):
        filename = self.arguments[0]

        cwd = os.getcwd()
        os.chdir(TMPDIR)

        show_header = not ("no_header" in self.arguments)
        show_bocks = not ("no_blocks" in self.arguments)

        parts = []
        try:
            ff = AsdfFile()
            with asdf.open(filename, ignore_unrecognized_tag=True, ignore_missing_extensions=True) as af:
                if af.version is None:
                    asdf_standard_version = version_string
                else:
                    asdf_standard_version = af.version

                file_version = af._file_format_version

            header_comments = (
                f"\n{ASDF_MAGIC.strip().decode('utf-8')} {file_version}\n"
                f"#{ASDF_STANDARD_COMMENT.strip().decode('utf-8')} {asdf_standard_version}\n"
            )

            code = AsdfFile._open_impl(ff, filename, _get_yaml_content=True)
            code = header_comments + code.strip().decode("utf-8")
            code += "\n"
            literal = nodes.literal_block(code, code)
            literal["language"] = "yaml"
            set_source_info(self, literal)
            if show_header:
                parts.append(literal)

            kwargs = dict()
            # Use the ignore_unrecognized_tag parameter as a proxy for both options
            kwargs["ignore_unrecognized_tag"] = "ignore_unrecognized_tag" in self.arguments
            kwargs["ignore_missing_extensions"] = "ignore_unrecognized_tag" in self.arguments

            if show_bocks:
                with asdf.open(filename, **kwargs) as ff:
                    for i, block in enumerate(ff._blocks.internal_blocks):
                        data = codecs.encode(block.data.tobytes(), "hex")
                        if len(data) > 40:
                            data = data[:40] + b"..."
                        allocated = block._allocated
                        size = block._size
                        data_size = block._data_size
                        flags = block._flags

                        if flags & BLOCK_FLAG_STREAMED:
                            allocated = size = data_size = 0

                        lines = []
                        lines.append(f"BLOCK {i}:")

                        human_flags = []
                        for key, val in FLAGS.items():
                            if flags & key:
                                human_flags.append(val)
                        if len(human_flags):
                            lines.append("    flags: {}".format(" | ".join(human_flags)))
                        if block.input_compression:
                            lines.append(f"    compression: {block.input_compression}")
                        lines.append(f"    allocated_size: {allocated}")
                        lines.append(f"    used_size: {size}")
                        lines.append(f"    data_size: {data_size}")
                        lines.append(f"    data: {data}")

                        code = "\n".join(lines)
                        code += "\n"

                        literal = nodes.literal_block(code, code)
                        literal["language"] = "yaml"
                        set_source_info(self, literal)
                        parts.append(literal)

                    internal_blocks = list(ff._blocks.internal_blocks)
                    if len(internal_blocks) and internal_blocks[-1].array_storage != "streamed":
                        buff = io.BytesIO()
                        ff._blocks.write_block_index(buff, ff)
                        block_index = buff.getvalue().decode("utf-8")
                        literal = nodes.literal_block(block_index, block_index)
                        literal["language"] = "yaml"
                        set_source_info(self, literal)
                        parts.append(literal)

        finally:
            os.chdir(cwd)

        result = nodes.admonition()
        textnodes, messages = self.state.inline_text(filename, self.lineno)
        title = nodes.title(filename, "", *textnodes)
        result += title
        result += parts
        return [result]
