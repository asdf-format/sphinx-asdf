"""
We aren't using the built in mistune math plugin here
to maintain consistency with the old custom markdown to
rst converter that used to be in this file.
"""

import re
import textwrap

import mistune
from mistune.renderers.rst import RSTRenderer


def inline_math_to_rst(renderer, content, block_state):
    return f":math:`{content['raw']}`"


def block_math_to_rst(renderer, content, block_state):
    out = ".. math::\n\n"
    out += "\n".join("   " + line for line in textwrap.dedent(content["raw"]).split("\n"))
    out += "\n\n"
    return out


def parse_inline_math(inline, m, state):
    text = m.group("math_text")
    state.append_token({"type": "inline_math", "raw": text})
    return m.end()


def parse_block_math(block, m, state):
    text = m.group("math_text")
    state.append_token({"type": "block_math", "raw": text})
    return m.end() + 1


def md2rst(content):
    renderer = RSTRenderer()
    renderer.register("inline_math", inline_math_to_rst)
    renderer.register("block_math", block_math_to_rst)
    converter = mistune.create_markdown(renderer=renderer)
    INLINE_MATH_PATTERN = r"\$\$?(?!\s)(?P<math_text>.+?)(?!\s)(?<!\\)\$\$?"
    converter.inline.register("inline_math", INLINE_MATH_PATTERN, parse_inline_math, before="link")
    BLOCK_MATH_PATTERN = r"\$\$(?P<math_text>[\w\W]*?)\$\$"
    converter.block.register("block_math", BLOCK_MATH_PATTERN, parse_block_math, before="list")
    return converter(content)
