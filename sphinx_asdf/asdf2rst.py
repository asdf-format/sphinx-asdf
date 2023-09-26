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
                exec(code, GLOBALS)  # noqa: S102
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


def _block_to_string(block):
    if hasattr(block, "header"):
        header = block.header
        data = block.data
    else:
        data = block.data
        header = {
            "flags": block._flags,
            "allocated_size": block._allocated,
            "used_size": block._size,
            "data_size": block._data_size,
            "compression": block.input_compression,
        }
    if header["flags"] & BLOCK_FLAG_STREAMED:
        header["allocated"] = header["used_size"] = header["data_size"] = 0

    # convert data to hex representation
    data = codecs.encode(data.tobytes(), "hex")
    if len(data) > 40:
        data = data[:40] + b"..."

    lines = []

    # convert header to string, add to lines
    human_flags = []
    for key, val in FLAGS.items():
        if header["flags"] & key:
            human_flags.append(val)
    if len(human_flags):
        lines.append(f"    flags: {' | '.join(human_flags)}")
    if header["compression"] and header["compression"] != b"\0\0\0\0":
        lines.append(f"    compression: {header['compression']}")
    lines.append(f"    allocated_size: {header['allocated_size']}")
    lines.append(f"    used_size: {header['used_size']}")
    lines.append(f"    data_size: {header['data_size']}")

    # add data as string to lines
    lines.append(f"    data: {data}")

    # add lines to code block
    code = "\n".join(lines)
    return code


class AsdfDirective(Directive):
    required_arguments = 1
    optional_arguments = 1

    def run(self):
        filename = self.arguments[0]

        cwd = os.getcwd()
        os.chdir(TMPDIR)

        show_header = "no_header" not in self.arguments
        show_bocks = "no_blocks" not in self.arguments

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
                    if hasattr(ff._blocks, "internal_blocks"):
                        blocks = list(ff._blocks.internal_blocks)
                    else:
                        blocks = ff._blocks.blocks

                    for i, block in enumerate(blocks):
                        code = "\n".join([f"BLOCK {i}:", _block_to_string(block), ""])
                        literal = nodes.literal_block(code, code)
                        literal["language"] = "yaml"
                        set_source_info(self, literal)
                        parts.append(literal)

                    # re-write out the block index
                    if len(blocks):
                        if hasattr(blocks[-1], "header"):
                            streamed = blocks[-1].header["flags"] & BLOCK_FLAG_STREAMED
                        else:
                            streamed = blocks[-1].array_storage == "streamed"
                        if not streamed:
                            # write out the block index
                            if hasattr(blocks[0], "header"):
                                block_index_offset = asdf._block.io.find_block_index(ff._fd)
                                buff = io.BytesIO()
                                ff._fd.seek(block_index_offset)
                                buff = io.BytesIO(ff._fd.read())
                            else:
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
