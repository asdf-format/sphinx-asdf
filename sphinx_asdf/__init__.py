import os

from sphinx.builders.html import StandaloneHTMLBuilder

from .asdf2rst import AsdfDirective, RunCodeDirective
from .connections import (
    add_labels_to_nodes,
    autogenerate_schema_docs,
    handle_page_context,
    on_build_finished,
    update_app_config,
)
from .directives import AsdfAutoschemas, AsdfSchema, schema_def
from .nodes import add_asdf_nodes


def setup(app):
    # Describes a path relative to the sphinx source directory
    app.add_config_value("asdf_schema_path", "schemas", "env")
    app.add_config_value("asdf_schema_standard_prefix", "", "env")
    app.add_config_value("asdf_schema_reference_mappings", [], "env")

    app.add_directive("asdf-autoschemas", AsdfAutoschemas)
    app.add_directive("asdf-schema", AsdfSchema)
    app.add_directive("runcode", RunCodeDirective)
    app.add_directive("asdf", AsdfDirective)

    add_asdf_nodes(app)

    app.connect("builder-inited", autogenerate_schema_docs)
    app.connect("config-inited", update_app_config)
    app.connect("html-page-context", handle_page_context)
    app.connect("doctree-read", add_labels_to_nodes)
    app.connect("build-finished", on_build_finished)

    static_dir = os.path.join(os.path.dirname(__file__), "static")

    app.config._raw_config.setdefault("html_static_path", []).append(static_dir)

    return dict(version="0.1.1", parallel_read_safe=True, parallel_write_safe=True)
