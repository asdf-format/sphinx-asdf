import logging
import os
import posixpath
import warnings

import docutils
import packaging.version
import sphinx.builders
from docutils import nodes
from sphinx.util import rst
from sphinx.util.docutils import sphinx_domains
from sphinx.util.fileutil import copy_asset

from .directives import schema_def
from .nodes import schema_doc

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates")

# docutils 0.19.0 fixed a bug in traverse/findall
# https://sourceforge.net/p/docutils/bugs/448/
# however sphinx-rtd-theme currently pins docutils to <0.19
# docutils has since deprecated traverse so for packages that don't
# use sphinx-rtd-theme (and will fetch 0.19.0) using findall will
# avoid the deprecation warnings
if packaging.version.parse(docutils.__version__) >= packaging.version.parse("0.19.0"):

    def traverse(doctree, *args, **kwargs):
        return doctree.findall(*args, **kwargs)

else:

    def traverse(doctree, *args, **kwargs):
        return doctree.traverse(*args, **kwargs)


def find_autoasdf_directives(env, filename):
    if filename.endswith(".md"):
        return []

    docname = env.path2doc(filename)
    env.prepare_settings(docname)
    with sphinx_domains(env), rst.default_role(docname, env.config.default_role):
        builder = sphinx.builders.text.TextBuilder(env.app, env)
        builder.read_doc(docname)
        doctree = env.get_and_resolve_doctree(docname, builder)

    return traverse(doctree, schema_def)


def find_autoschema_references(app, genfiles):
    # We set this environment variable to indicate that the AsdfSchemas
    # directive should be parsed as a simple list of schema references
    # rather than as the toctree that will be generated when the documentation
    # is actually built.
    app.env.autoasdf_generate = True

    logger = logging.getLogger("sphinx")
    orig_level = logger.getEffectiveLevel()
    logger.setLevel(logging.ERROR)

    schemas = set()
    for fn in genfiles:
        # Create documentation files based on contents of asdf-schema directives
        path = posixpath.join(app.env.srcdir, fn)
        app.env.temp_data["docname"] = app.env.path2doc(path)
        schemas = schemas.union(find_autoasdf_directives(app.env, path))

    logger.setLevel(orig_level)

    # Unset this variable now that we're done.
    app.env.autoasdf_generate = False

    return list(schemas)


def create_schema_docs(app, schemas):
    for schema in schemas:
        schema_name = schema.children[0].astext()
        standard_prefix = schema.standard_prefix or app.env.config.asdf_schema_standard_prefix
        output_dir = posixpath.join(app.srcdir, "generated", standard_prefix)
        doc_path = posixpath.join(output_dir, schema_name + ".rst")

        if posixpath.exists(doc_path):
            continue

        os.makedirs(posixpath.dirname(doc_path), exist_ok=True)

        with open(doc_path, "w") as ff:
            ff.write(f".. _{standard_prefix}/{schema_name}:\n\n")
            ff.write(schema_name + "\n")
            ff.write("=" * len(schema_name) + "\n\n")
            ff.write(".. asdf-schema::\n")
            if standard_prefix:
                ff.write(f"    :standard_prefix: {standard_prefix}\n")
            ff.write(f"    :schema_root: {schema.schema_root}\n\n")
            ff.write(f"    {schema_name}\n")


def autogenerate_schema_docs(app):
    env = app.env

    genfiles = [env.doc2path(x, base=None) for x in env.found_docs if posixpath.isfile(env.doc2path(x))]

    if not genfiles:
        return

    ext = list(app.config.source_suffix)
    genfiles = [genfile + (not genfile.endswith(tuple(ext)) and ext[0] or "") for genfile in genfiles]

    # Read all source documentation files and parse all asdf-schema directives
    schemas = find_autoschema_references(app, genfiles)
    # Create the documentation files that correspond to the schemas listed
    create_schema_docs(app, schemas)


def update_app_config(app, config):
    from pkg_resources import get_distribution

    dist = get_distribution("sphinx_asdf")
    config.html_context["sphinx_asdf_version"] = dist.version


def handle_page_context(app, pagename, templatename, ctx, doctree):
    # Use custom template when rendering pages containing schema documentation.
    # This allows us to selectively include bootstrap
    if doctree is not None and traverse(doctree, schema_doc):
        return os.path.join(TEMPLATE_PATH, "schema.html")


def normalize_name(name):
    for char in [".", "_", "/"]:
        name = name.replace(char, "-")
    return name


def add_labels_to_nodes(app, document):
    labels = app.env.domaindata["std"]["labels"]
    anonlabels = app.env.domaindata["std"]["anonlabels"]
    basepath = os.path.join("generated", app.env.config.asdf_schema_standard_prefix)

    for node in traverse(document):
        if isinstance(node, str) or not (isinstance(node, nodes.Node) and node["ids"]):
            continue

        labelid = node["ids"][0]
        docname = app.env.docname
        basename = os.path.relpath(docname, basepath)

        if labelid == normalize_name(basename):
            name = basename
        else:
            name = nodes.fully_normalize_name(basename + ":" + labelid)

        # labelname -> docname, labelid
        anonlabels[name] = docname, labelid
        # labelname -> docname, labelid, sectionname
        labels[name] = docname, labelid, ""


def on_build_finished(app, exc):
    if exc is None:
        for asset in ["sphinx_asdf.css", "sphinx_asdf.js"]:
            src = posixpath.join(posixpath.dirname(__file__), "static", asset)
            dst = posixpath.join(app.outdir, "_static")
            copy_asset(src, dst)
