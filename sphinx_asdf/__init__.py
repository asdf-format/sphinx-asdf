from .nodes import add_asdf_nodes
from .directives import AsdfAutoschemas, AsdfSchema, schema_def
from .connections import (autogenerate_schema_docs, add_labels_to_nodes,
                          on_build_finished)



def setup(app):

    # Describes a path relative to the sphinx source directory
    app.add_config_value('asdf_schema_path', 'schemas', 'env')
    app.add_config_value('asdf_schema_standard_prefix', '', 'env')
    app.add_directive('asdf-autoschemas', AsdfAutoschemas)
    app.add_directive('asdf-schema', AsdfSchema)

    add_asdf_nodes(app)

    app.add_css_file('sphinx_asdf.css')
    app.add_javascript('sphinx_asdf.js')

    app.connect('builder-inited', autogenerate_schema_docs)
    app.connect('doctree-read', add_labels_to_nodes)
    app.connect('build-finished', on_build_finished)

    return dict(version='0.1')
