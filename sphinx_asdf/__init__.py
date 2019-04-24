import os

from .nodes import add_asdf_nodes
from .directives import AsdfAutoschemas, AsdfSchema, schema_def
from .connections import (autogenerate_schema_docs, update_app_config,
                          handle_page_context, add_labels_to_nodes,
                          on_build_finished)

from sphinx.builders.html import StandaloneHTMLBuilder


def setup(app):

    # Describes a path relative to the sphinx source directory
    app.add_config_value('asdf_schema_path', 'schemas', 'env')
    app.add_config_value('asdf_schema_standard_prefix', '', 'env')
    app.add_config_value('asdf_schema_reference_mappings', [], 'env')

    app.add_directive('asdf-autoschemas', AsdfAutoschemas)
    app.add_directive('asdf-schema', AsdfSchema)

    add_asdf_nodes(app)

    app.connect('builder-inited', autogenerate_schema_docs)
    app.connect('config-inited', update_app_config)
    app.connect('html-page-context', handle_page_context)
    app.connect('doctree-read', add_labels_to_nodes)
    app.connect('build-finished', on_build_finished)

    return dict(version='0.1')
