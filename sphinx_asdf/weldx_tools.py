import posixpath
from pprint import pformat

import yaml

from docutils import nodes
from docutils.statemachine import ViewList
from docutils.parsers.rst import directives

from sphinx import addnodes
from sphinx.util.nodes import nested_parse_with_titles
from sphinx.util.docutils import SphinxDirective

from .md2rst import md2rst
from .nodes import (toc_link, schema_doc, schema_header_title, schema_title,
                    schema_description, schema_properties, schema_property,
                    schema_property_name, schema_property_details,
                    schema_combiner_body, schema_combiner_list,
                    schema_combiner_item, section_header, asdf_tree, asdf_ref,
                    example_section, example_item, example_description)


def make_wx_node(schema, key, default_flow_style=False):
    entry = schema[key]
    if isinstance(entry, dict):
        default_node = nodes.compound()
        default_node.append(nodes.line(text=key + ":"))
        default_node.append(nodes.literal_block(
            text=yaml.dump(entry, default_flow_style=default_flow_style),
            language='yaml'))
        return default_node
    else:
        text = f'{key}: {entry}'
        return nodes.line(text=text)
